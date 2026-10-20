import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from studio import autonomous as auto
from studio import paid_requests as paid
from studio.production import production_lock, ProductionBusy, lease_fds, child_environment
from studio.learning import save_lesson, load_lessons
from studio.asset_adaptation import find_assets, plan_adaptation, adapt_asset


class ManagedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'videos/videofactory/demo'
        self.project.mkdir(parents=True)
        (self.project / 'project.json').write_text('{"brand":"videofactory"}')
        self.settings = dict(brand='videofactory', subject='A task', intended_result='Explain the task',
                             format='tall', language='en', review_mode='autonomous', max_paid_spend=3)

    def write(self, name, data):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)

    def runner(self, root, project, stage, context):
        if stage == 'render':
            self.write('05_render/demo.mp4', 'media')
            self.write('05_render/sheets/sheet.png', 'frame')
            self.write('05_render/demo-cover.jpg', 'cover')
            self.write('05_render/DESCRIPTION.md', 'ai_label: false\nA useful description.')
            self.write('04_scene/assets/sound.md', 'Music: CC0, verified source')
        elif stage == 'critic':
            hashes = auto.review_artifacts(project)
            self.write('05_render/critic.json', json.dumps(dict(critic_id='separate-critic',
                scores=dict.fromkeys(auto.SCORES, 9), blocking_issues=[], evidence=['frame at 0s'],
                artifact_hashes=hashes, audio_review=dict(listened=True, evidence=['audio at 1s'],
                    artifact_sha256=hashes['05_render/demo.mp4']))))
        elif stage == 'package': auto._package(project, context)
        elif stage == 'checks': self.write('05_render/check.md', 'page errors    0\nframes checked (info)    48\n')
        elif stage == 'transcript':
            self.write('02_transcript/words.json', '{"duration":2,"words":[{"text":"hello","start":0,"end":1}]}')
            self.write('02_transcript/transcript.md', 'hello')
        elif stage == 'cues':
            self.write('03_cues/cues.json', '{"cueList":[{"start":0}]}')
            self.write('03_cues/cues.md', '## opening "hello"')
        else:
            for name in auto.OUTPUTS[stage]: self.write(name, 'This is complete authored content.')
            if stage == 'scene': self.write('04_scene/assets/sound.md', 'Music: CC0, verified source')

    def run_mocked(self, **kwargs):
        with patch.object(auto, 'stage_runner', side_effect=self.runner), patch.object(auto, '_render_valid', return_value=True):
            return auto.run_video(self.root, 'videofactory/demo', **kwargs)

    def test_complete_resume_and_input_invalidation(self):
        run = self.run_mocked(settings=self.settings)
        self.assertEqual(run['status'], 'ready-for-final-review')
        with patch.object(auto, 'stage_runner', side_effect=AssertionError('Must reuse artifacts')), patch.object(auto, '_render_valid', return_value=True):
            resumed = auto.run_video(self.root, 'videofactory/demo', resume=run['id'])
        self.assertEqual(resumed['status'], 'ready-for-final-review')
        self.write('04_scene/scene.js', 'Changed scene')
        calls = []
        def changed(*args): calls.append(args[2]); return self.runner(*args)
        with patch.object(auto, 'stage_runner', side_effect=changed), patch.object(auto, '_render_valid', return_value=True):
            auto.run_video(self.root, 'videofactory/demo', resume=run['id'])
        self.assertIn('scene', calls)
        self.assertIn('critic', calls)

    def test_selected_review_stops_without_approval(self):
        settings = self.settings | dict(review_mode='selected-stages', selected_stages=['brief'])
        with patch.object(auto, '_approved', return_value=False): run = self.run_mocked(settings=settings)
        self.assertEqual(run['status'], 'waiting-for-review')
        self.assertNotIn('script', run['stages'])

    def test_final_review_mode_and_missing_output(self):
        run = self.run_mocked(settings=self.settings | dict(review_mode='final-review-only'))
        self.assertEqual(run['status'], 'ready-for-final-review')
        with patch.object(auto, 'stage_runner', return_value=None):
            run = auto.run_video(self.root, 'videofactory/demo', settings=self.settings | dict(research=True))
        self.assertEqual(run['status'], 'needs-attention')

    def test_critic_rejects_stale_low_and_unheard(self):
        run = self.run_mocked(settings=self.settings)
        report = json.loads((self.project / '05_render/critic.json').read_text())
        self.assertTrue(auto.critic_valid(self.project, report, run['builder_id']))
        report['scores']['hook'] = 7
        self.assertFalse(auto.critic_valid(self.project, report, run['builder_id']))
        report['scores']['hook'] = 9
        report['audio_review']['listened'] = False
        self.assertFalse(auto.critic_valid(self.project, report, run['builder_id']))
        report['audio_review']['listened'] = True
        self.write('05_render/demo.mp4', 'new media')
        self.assertFalse(auto.critic_valid(self.project, report, run['builder_id']))

    def test_budget_unknown_uncertain_duplicate_and_limit(self):
        ident = 'a' * 32
        paid.atomic_json(self.root / '.studio/runs' / (ident + '.json'), dict(settings=self.settings))
        with self.assertRaises(paid.BudgetError): paid.reserve(self.root, ident, 'unknown', None)
        with self.assertRaises(RuntimeError):
            paid.guarded_call(self.root, ident, 'first', 2, lambda: (_ for _ in ()).throw(RuntimeError()))
        with self.assertRaises(paid.BudgetError): paid.reserve(self.root, ident, 'second', 1)
        paid.reconcile(self.root, ident, 'first', 2)
        with self.assertRaises(paid.BudgetError): paid.reserve(self.root, ident, 'first', 0)
        paid.guarded_call(self.root, ident, 'second', 1, lambda: 'ok')
        with self.assertRaises(paid.BudgetError): paid.reserve(self.root, ident, 'third', '.01')

    def test_thread_and_process_contention(self):
        errors = []
        with production_lock(self.root):
            def attempt():
                try:
                    with production_lock(self.root): pass
                except ProductionBusy: errors.append(True)
            thread = threading.Thread(target=attempt)
            thread.start(); thread.join()
            result = subprocess.run([sys.executable, '-c',
                'from studio.production import production_lock; import sys\nwith production_lock(sys.argv[1]): pass', str(self.root)],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        self.assertEqual(errors, [True])
        with production_lock(self.root): self.assertTrue(lease_fds())

    def test_inherited_lease_reentry(self):
        with production_lock(self.root):
            result = subprocess.run([sys.executable, '-c',
                'from studio.production import production_lock; import sys\nwith production_lock(sys.argv[1]): pass', str(self.root)],
                capture_output=True, text=True, env=os.environ | child_environment(self.root), pass_fds=lease_fds())
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_adaptation_private_and_claims_require_evidence(self):
        (self.root / '.env').write_text('secret')
        validation = dict(target_brand='target', evidence=['checked source identity and claims'], identity_removed=True, claims_verified=True)
        with self.assertRaises(ValueError):
            adapt_asset(self.root, '.env', 'videofactory', 'target', rights='own', changes=['color'], validation=validation)
        path = self.root / 'brands/videofactory/library/icon.svg'
        path.parent.mkdir(parents=True)
        path.write_text('<svg fill="{{TOKEN:primary}}"/>')
        with self.assertRaises(ValueError):
            adapt_asset(self.root, 'brands/videofactory/library/icon.svg', 'videofactory', 'target', rights='own', changes=['color'], tokens={'primary':'blue'}, source_kind='icon')
        record = adapt_asset(self.root, 'brands/videofactory/library/icon.svg', 'videofactory', 'target', rights='own', changes=['color'], tokens={'primary':'blue'}, source_kind='icon', validation=validation)
        self.assertEqual(record['status'], 'draft')
        self.assertEqual((self.root / record['artifact']).read_text(), '<svg fill="blue"/>')
        self.assertFalse(record['user_approved'])

    def test_critic_repairs_at_most_three_times(self):
        counts = []
        def runner(*args):
            self.runner(*args)
            if args[2] == 'critic':
                counts.append(True)
                path = self.project / '05_render/critic.json'
                report = json.loads(path.read_text())
                report['scores']['hook'] = 7
                path.write_text(json.dumps(report))
        with patch.object(auto, 'stage_runner', side_effect=runner), patch.object(auto, '_render_valid', return_value=True):
            run = auto.run_video(self.root, 'videofactory/demo', settings=self.settings)
        self.assertEqual(run['status'], 'needs-attention')
        self.assertEqual(run['repair_rounds'], 3)
        self.assertEqual(len(counts), 4)

    def test_learning_and_brand_asset_order(self):
        save_lesson(self.root, dict(lesson='Avoid overlap', evidence=['review:1'], status='verified', stages=['scene']))
        save_lesson(self.root, dict(lesson='New brand rule', evidence=['review:2'], status='verified', kind='brand-rule'), brand='videofactory')
        self.assertEqual(len(load_lessons(self.root, 'videofactory', 'scene')), 1)
        self.assertEqual(load_lessons(self.root, 'videofactory', 'script'), [])
        for scope in ('brands/videofactory/library', 'library'):
            paid.atomic_json(self.root / scope / 'INDEX.json', [dict(title='Example')])
        assets = find_assets(self.root, 'videofactory', 'Example')
        self.assertTrue(assets[0]['record_path'].startswith('brands/videofactory/'))
        self.write('04_scene/photo.png', 'raster')
        with self.assertRaises(ValueError):
            plan_adaptation(self.root, 'videos/videofactory/demo/04_scene/photo.png', 'videofactory', 'other', rights='own', changes=['colors'], token_restyle=True)

    def test_default_dispatch_for_mechanical_stages(self):
        commands = []
        context = dict(run_id='a'*32, video_id='videofactory/demo', settings=self.settings | dict(paid_quotes={'x': {'max_cost':1,'evidence':'quote'}}))
        with patch.object(auto, '_command', side_effect=lambda root,argv,env: commands.append(argv)), \
             patch('studio.jobs._contained_browser', return_value=('box-123','http://localhost:1')), \
             patch('studio.jobs._stop_box'):
            for stage in ('voice', 'transcript', 'checks', 'render'):
                auto._default_runner(self.root, self.project, stage, context)
        self.assertEqual([a[2] for a in commands if a[0] != 'ffmpeg'], ['speak','transcribe','check','render','stills','listen'])
        self.assertIn(['--language','en'], [a[-2:] for a in commands if 'transcribe' in a])

    def test_full_default_dispatch_with_mocked_workers_and_paid_provider(self):
        calls = []
        def command(root, argv, env):
            calls.append(argv)
            run = json.loads((self.root / '.studio/runs' / (env['VF_RUN_ID']+'.json')).read_text())
            context = dict(run_id=run['id'],video_id=run['video_id'],settings=run['settings'],builder_id=run['builder_id'])
            if argv[0] == 'claude': stage = re.search(r'Produce only stage (\w+)',argv[2])[1]
            elif argv[0] == 'ffmpeg': return
            else:
                stage = {'speak':'voice','transcribe':'transcript','check':'checks','render':'render','cues':'cues'}.get(argv[2])
            if stage == 'voice':
                paid.guarded_call(self.root,run['id'],'mock-voice-request',1,lambda:b'audio',provider='mock',purpose='voice')
            if stage: self.runner(root,self.project,stage,context)
        with patch.object(auto,'stage_runner',auto._default_runner), patch.object(auto,'_command',side_effect=command), \
             patch.object(auto.shutil,'which',return_value='/mock/claude'), \
             patch.object(auto,'_render_valid',return_value=True), \
             patch('studio.jobs._contained_browser',return_value=('box-123','http://localhost:1')), patch('studio.jobs._stop_box'):
            run = auto.run_video(self.root,'videofactory/demo',settings=self.settings)
        self.assertEqual(run['status'],'ready-for-final-review')
        ledger = json.loads((self.root / '.studio/paid' / (run['id']+'.json')).read_text())
        self.assertEqual(ledger['requests']['mock-voice-request']['actual_cost'],'1')
        self.assertEqual(len([a for a in calls if a[0]=='claude']),5)

    def test_package_hashes_and_generated_voice_disclosure(self):
        self.run_mocked(settings=self.settings)
        self.assertTrue(auto._package_valid(self.project))
        self.write('05_render/demo-cover.jpg', 'changed cover')
        self.assertFalse(auto._package_valid(self.project))
        self.write('01_voice/takes/01.json', '{}')
        with self.assertRaises(ValueError): auto._package(self.project, dict(run_id='a'*32))
        self.write('05_render/DESCRIPTION.md', 'ai_label: true\nDescription\nVoice-over made with AI.')
        auto._package(self.project, dict(run_id='a'*32))
        self.assertTrue(auto._package_valid(self.project))

    def test_quote_after_price_discovery_and_explicit_retry(self):
        ident = 'c'*32
        paid.atomic_json(self.root / '.studio/runs' / (ident+'.json'), dict(settings=self.settings))
        with patch.dict(os.environ, dict(VF_PAID_GUARD='1',VF_RUN_ROOT=str(self.root),VF_RUN_ID=ident)):
            with self.assertRaisesRegex(paid.BudgetError, 'logical-request'):
                paid.managed_quote(self.root,'logical-request',purpose='voice',metadata={'characters':50})
            paid.record_quote(self.root,ident,'logical-request',1,'provider maximum price')
            run_id, quote = paid.managed_quote(self.root,'logical-request')
            paid.reserve(self.root,run_id,quote['request_id'],quote['max_cost'])
            with self.assertRaises(paid.BudgetError): paid.record_quote(self.root,ident,'logical-request',1,'retry',retry=True)
            paid.reconcile(self.root,ident,'logical-request',1,evidence='provider receipt')
            retry = paid.record_quote(self.root,ident,'logical-request',1,'new quoted attempt',retry=True)
            self.assertNotEqual(retry['request_id'],'logical-request')
            self.assertEqual(paid.managed_quote(self.root,'logical-request')[1]['request_id'], retry['request_id'])

    def test_paid_bundle_mirrors_pending_quote_and_charge(self):
        ident = 'd'*32
        paid.atomic_json(self.root / '.studio/runs' / (ident+'.json'),
                         dict(id=ident, video_id='videofactory/demo', settings=self.settings))
        bundle = self.project / 'runs' / ident / 'paid'
        with patch.dict(os.environ, dict(VF_PAID_GUARD='1',VF_RUN_ROOT=str(self.root),VF_RUN_ID=ident)):
            with self.assertRaises(paid.BudgetError): paid.managed_quote(self.root,'voice-request',purpose='voice')
        self.assertEqual(json.loads((bundle / 'voice-request.pending.json').read_text())['state'],'needs-quote')
        quote = paid.record_quote(self.root,ident,'voice-request',1,'verified provider maximum')
        self.assertEqual(json.loads((bundle / 'quotes.json').read_text())['voice-request'],quote)
        paid.guarded_call(self.root,ident,'voice-request',1,lambda:b'audio')
        ledger = json.loads((self.root / '.studio/paid' / (ident+'.json')).read_text())
        self.assertEqual(json.loads((bundle / 'ledger.json').read_text()),ledger)
        self.assertEqual(ledger['requests']['voice-request']['actual_cost'],'1')

    def test_malformed_critic_resume_recovers(self):
        run = self.run_mocked(settings=self.settings)
        self.write('05_render/critic.json','{broken')
        run = self.run_mocked(resume=run['id'])
        self.assertEqual(run['status'],'ready-for-final-review')

    def test_quoted_image_requests_and_timeout_reservation(self):
        from studio import generation
        ident = 'b' * 32
        record = dict(billing_acknowledged=True, requested_image_model='gpt-image-2', transparent=False,
                      output_dir='styles/demo/generated', outputs=[], image_count=1,
                      resolved_references=[], prompt='A blue shape', purpose='style-material')
        request_id = generation.image_request_id(record, 1)
        runpath = self.root / '.studio/runs' / (ident + '.json')
        paid.atomic_json(runpath, dict(settings=self.settings | dict(paid_quotes={request_id: dict(max_cost=1,evidence='provider maximum quote')})))
        script = self.root / 'image_gen.py'; script.write_text('')
        env = dict(VF_PAID_GUARD='1',VF_RUN_ROOT=str(self.root),VF_RUN_ID=ident,OPENAI_API_KEY='fake')
        with patch.dict(os.environ, env), patch.object(generation,'_API_SCRIPT',script), \
             patch.object(generation.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')):
            result = generation._run_api(self.root,record)
        ledger = json.loads((self.root / '.studio/paid' / (ident+'.json')).read_text())
        self.assertEqual(ledger['requests'][request_id]['state'],'settled')
        self.assertEqual(len(result['outputs']),1)
        record['prompt'] = 'Changed shape'
        with patch.dict(os.environ, env), patch.object(generation,'_API_SCRIPT',script):
            with self.assertRaises(paid.BudgetError): generation._run_api(self.root,record)
        request_id = generation.image_request_id(record,1)
        run = json.loads(runpath.read_text())
        run['settings']['paid_quotes'][request_id] = dict(max_cost=1,evidence='provider maximum quote')
        paid.atomic_json(runpath,run)
        with patch.dict(os.environ, env), patch.object(generation,'_API_SCRIPT',script), \
             patch.object(generation.subprocess,'run',side_effect=subprocess.TimeoutExpired([],900)):
            generation._run_api(self.root,record)
        ledger = json.loads((self.root / '.studio/paid' / (ident+'.json')).read_text())
        self.assertEqual(ledger['requests'][request_id]['state'],'reserved')


if __name__ == '__main__': unittest.main()
