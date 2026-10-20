"""Managed, resumable production. Validation never grants approval: a person does."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import uuid

from studio.paid_requests import atomic_json, money
from studio.production import production_lock, lease_fds, child_environment
from studio.learning import load_lessons, record_learning

STAGES = ('research', 'brief', 'script', 'voice', 'transcript', 'cues', 'scene', 'checks', 'render', 'critic', 'package')
SCORES = ('hook', 'readability', 'motion', 'variety', 'composition', 'accuracy', 'sound_sync')
OUTPUTS = {
 'research': ('00_research/research.md',), 'brief': ('01_voice/brief.md',),
 'script': ('01_voice/script.md',), 'voice': ('01_voice/voice.mp3',),
 'transcript': ('02_transcript/words.json', '02_transcript/transcript.md'),
 'cues': ('03_cues/cues.md', '03_cues/cues.json'),
 'scene': ('04_scene/scene.js',), 'checks': ('05_render/check.md',),
 'render': ('05_render/video.mp4',), 'critic': ('05_render/critic.json',), 'package': ('05_render/package.json',)}


def validate_settings(settings):
    if not isinstance(settings, dict): raise ValueError('Run settings are required.')
    result = dict(settings)
    for field in ('brand', 'subject', 'intended_result', 'format', 'language'):
        if not isinstance(result.get(field), str) or not result[field].strip():
            raise ValueError(field + ' is required.')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', result['brand']): raise ValueError('Invalid brand.')
    if result.get('review_mode') not in ('autonomous', 'final-review-only', 'selected-stages'):
        raise ValueError('Select a review mode.')
    selected = result.setdefault('selected_stages', [])
    if not isinstance(selected, list) or any(s not in ('research','brief','script','voice','transcript','cues','scene','render') for s in selected):
        raise ValueError('Selected review stages are invalid.')
    if result['format'] not in ('wide', 'tall'): raise ValueError('Format must be wide or tall.')
    result['max_paid_spend'] = str(money(result.get('max_paid_spend')))
    result.setdefault('research', False)
    if type(result['research']) is not bool: raise ValueError('Research must be true or false.')
    return result


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _dependencies(root, project, brand):
    paths = [project / 'project.json', project / 'settings.json', project / 'materials.md']
    for directory in (root / '_runtime', root / '_shared', root / 'brands' / brand):
        if directory.is_dir():
            paths += [p for p in directory.rglob('*') if p.is_file() and p.suffix in ('.js', '.json', '.css', '.md', '.html')]
    return {str(p.relative_to(root)): _hash(p) for p in sorted(paths) if p.is_file()}


def _artifacts(project, stage):
    paths = [project / p for p in OUTPUTS[stage]]
    if stage == 'scene' and not paths[0].exists(): paths = [project / '04_scene/index.html']
    if stage == 'scene': paths += [p for p in sorted((project / '04_scene').rglob('*')) if p.is_file() and p not in paths and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.log','.tmp')]
    if stage == 'voice': paths = [p for p in (project / '01_voice').glob('voice.*') if p.suffix in ('.mp3','.wav','.m4a','.flac','.ogg','.aac')]
    if stage == 'render': paths = [project / '05_render' / (project.name + '.mp4')]
    return {str(p.relative_to(project)): _hash(p) for p in paths if p.is_file() and p.stat().st_size}


def _valid(project, stage):
    artifacts = _artifacts(project, stage)
    if len(artifacts) < len(OUTPUTS[stage]): return False
    try:
        if stage in ('brief', 'script', 'research'):
            from studio.workspace import _substantive
            return all(_substantive(project / p) for p in OUTPUTS[stage])
        if stage == 'transcript':
            words = json.loads((project / '02_transcript/words.json').read_text())
            duration = float(words['duration'])
            if not math.isfinite(duration) or duration <= 0 or not isinstance(words['words'], list) or not words['words']: return False
            last = 0
            for word in words['words']:
                start, end = float(word['start']), float(word['end'])
                if not word.get('text') or not all(math.isfinite(t) for t in (start,end)) or not last <= start < end <= duration: return False
                last = start
            return True
        if stage == 'cues': return bool(json.loads((project / '03_cues/cues.json').read_text()))
        if stage == 'checks':
            text = (project / '05_render/check.md').read_text()
            counters = re.findall(r'^([^\n]+?)\s{2,}(\d+)\s*$', text, re.M)
            counters = [(name, n) for name, n in counters if '(info)' not in name]
            return bool(counters) and all(int(n) == 0 for _, n in counters)
        if stage == 'render': return _render_valid(project)
        if stage == 'package': return _package_valid(project)
    except (ValueError, KeyError, TypeError): return False
    return True


def _render_valid(project):
    from studio.workspace import _video_check_ok, _audio_check_ok
    video = project / '05_render' / (project.name + '.mp4')
    try:
        return _video_check_ok(project / '05_render/check-video.md') and _audio_check_ok(project, video)
    except (OSError, ValueError, KeyError): return False


def critic_valid(project, report, builder):
    if not isinstance(report, dict) or not report.get('critic_id') or report['critic_id'] == builder:
        return False
    scores = report.get('scores', {})
    if set(scores) != set(SCORES) or any(type(v) not in (int, float) or not 8 <= v <= 10 for v in scores.values()): return False
    if report.get('blocking_issues') != []: return False
    expected = review_artifacts(project)
    final = '05_render/' + Path(project).name + '.mp4'
    if final not in expected or not any(p.startswith('05_render/sheets/') for p in expected): return False
    if report.get('artifact_hashes') != expected: return False
    audio = report.get('audio_review', {})
    return (audio.get('listened') is True and bool(audio.get('evidence')) and
            audio.get('artifact_sha256') == expected[final] and bool(report.get('evidence')))


def review_artifacts(project):
    project = Path(project)
    paths = list((project / '05_render').glob('*.mp4'))
    paths += list((project / '05_render/sheets').glob('*.png'))
    paths += [p for p in (project / '01_voice').glob('voice.*') if p.suffix in ('.mp3','.wav','.m4a','.flac','.ogg','.aac')]
    return {str(p.relative_to(project)): _hash(p) for p in sorted(paths) if p.is_file()}


def _command(root, argv, env):
    env = env | child_environment(root)
    process = subprocess.Popen(argv, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, pass_fds=lease_fds(), start_new_session=True)
    worker_path = None
    out = err = ''
    run_id = env.get('VF_RUN_ID', '')
    if re.fullmatch(r'[a-f0-9]{32}', run_id):
        from studio.jobs import _process_start
        worker_path = Path(root) / '.studio/runs' / (run_id + '.worker.json')
        atomic_json(worker_path, dict(state='running', pid=process.pid, process_group=process.pid,
                    process_start=_process_start(process.pid), controller_pid=os.getpid()))
    try:
        out, err = process.communicate(timeout=1800)
    except BaseException:
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        out, err = process.communicate()
        raise
    finally:
        # A successful parent must not leave background agents with a live lease.
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        process.wait(timeout=10)
        if worker_path:
            atomic_json(worker_path, dict(state='exited', pid=process.pid, process_group=process.pid,
                        group_stop='SIGKILL sent; inherited production lease remains authoritative'))
            from studio.jobs import _secret_values
            from studio.project_paths import resolve_project
            secrets = _secret_values(root)
            def clean(text):
                for secret in secrets:
                    if secret: text = text.replace(secret, '[redacted]')
                return text[:1_048_576]
            run = json.loads((Path(root) / '.studio/runs' / (run_id + '.json')).read_text())
            project = resolve_project(root, run['video_id'])
            atomic_json(project / 'runs' / run_id / 'commands' / (uuid.uuid4().hex + '.json'),
                        dict(argv=[clean(str(a)) for a in argv], stdout=clean(out or ''), stderr=clean(err or ''),
                             exit_code=process.returncode, pid=process.pid))
    if process.returncode: raise RuntimeError((err or out)[-1500:] or 'Stage command failed.')
    return subprocess.CompletedProcess(argv, process.returncode, out, err)


def _default_runner(root, project, stage, context):
    env = os.environ | {'VF_RUN_ID': context['run_id'], 'VF_RUN_ROOT': str(root), 'VF_PAID_GUARD': '1',
                        'DISPLAY': '', 'WAYLAND_DISPLAY': 'omabox-guard'}
    python = str(root / '.venv/bin/python') if (root / '.venv/bin/python').exists() else sys.executable
    cli = [python, 'anim.py']
    ident = context['video_id']
    if stage == 'transcript': _command(root, cli + ['transcribe', ident, '--force', '--language', context['settings']['language']], env); return
    if stage in ('checks', 'render'):
        from studio.jobs import _contained_browser, _stop_box
        name, endpoint = _contained_browser()
        try:
            _command(root, cli + (['check', ident] if stage == 'checks' else ['render', ident, '--phone']),
                     env | {'ANIM_CDP_URL': endpoint})
            if stage == 'render':
                _command(root, cli + ['stills', ident], env | {'ANIM_CDP_URL': endpoint})
                _command(root, cli + ['listen', ident], env)
                _command(root, ['ffmpeg', '-y', '-ss', '0.8', '-i',
                         str(project / '05_render' / (project.name + '.mp4')),
                         '-frames:v', '1', str(project / '05_render' / (project.name + '-cover.jpg'))], env)
        finally: _stop_box(name)
        return
    if stage == 'voice':
        if _valid(project, stage) and _approved(root, ident, 'voice'): return
        _command(root, cli + ['speak', ident], env)
        return
    if stage == 'package':
        if (project / '05_render/DESCRIPTION.md').is_file():
            _package(project, context); return
    prompt = (f"Produce only stage {stage} for {project.relative_to(root)}. Read AGENTS.md and the stage contract. "
              f"Run settings and relevant lessons: {json.dumps(context, ensure_ascii=False)}. "
              "Do not approve gates. Do not publish. Do not call paid tools or APIs. Do not run a render now. "
              "Write real stage artifacts. Do not treat a successful process exit as validation. ")
    if stage == 'critic':
        prompt += ("You are an independent read-only critic; do not repair the video. Follow .claude/agents/frame-critic.md. "
                   "Save 05_render/critic.json with critic_id, scores (hook/readability/motion/variety/composition/accuracy/sound_sync), "
                   "blocking_issues, evidence, artifact_hashes and audio_review {listened,evidence,artifact_sha256}. "
                   "Only claim listened after actual audio playback. If unavailable, record listened:false. "
                   f"Current hashes: {json.dumps(review_artifacts(project))}")
    if stage == 'package':
        prompt += ('Write 05_render/DESCRIPTION.md using only verified script and brief facts. Include a clear ai_label: true/false decision, '
                   'and the required Voice-over made with AI. line when voice is generated. Do not invent sources, rights or evidence.')
    if not shutil.which('claude'): raise ValueError('The stage worker is not installed.')
    allowed = ['Read', 'Edit', 'Write', 'Glob', 'Grep'] + (['WebFetch', 'WebSearch'] if stage == 'research' else [])
    denied = ['Bash'] + ([] if stage == 'research' else ['WebFetch', 'WebSearch'])
    _command(root, ['claude', '-p', prompt, '--permission-mode', 'acceptEdits',
                    '--allowedTools', *allowed, '--disallowedTools', *denied], env)
    if stage == 'cues': _command(root, cli + ['cues', ident], env)
    if stage == 'package': _package(project, context)


# One replaceable boundary for tests and other local agent tools.
stage_runner = _default_runner


def _package(project, context):
    render = project / '05_render'
    video = render / (project.name + '.mp4')
    required = {'video': video, 'cover': render / (project.name + '-cover.jpg'),
                'description': render / 'DESCRIPTION.md', 'credits': project / '04_scene/assets/sound.md'}
    if any(p is None or not p.is_file() or not p.stat().st_size for p in required.values()):
        raise ValueError('Export needs video, cover, description and sound credits.')
    description = required['description'].read_text()
    decision = re.search(r'^ai_label:\s*(true|false)\s*$', description, re.M)
    if not decision: raise ValueError('The description needs an explicit AI disclosure decision.')
    generated = any((project / '01_voice/takes').glob('*.json'))
    if generated and (decision[1] != 'true' or not description.rstrip().endswith('Voice-over made with AI.')):
        raise ValueError('Generated voice needs the AI label and final voice disclosure line.')
    atomic_json(render / 'package.json', dict(status='ready-for-review',
                files={k: dict(path=str(p.relative_to(project)), sha256=_hash(p)) for k,p in required.items()},
                critic_sha256=_hash(render / 'critic.json'), disclosure=description,
                run_id=context['run_id']))


def _package_valid(project):
    try:
        package = json.loads((project / '05_render/package.json').read_text())
        if package.get('status') != 'ready-for-review': return False
        if package['critic_sha256'] != _hash(project / '05_render/critic.json'): return False
        expected = dict(video='05_render/' + project.name + '.mp4', cover='05_render/' + project.name + '-cover.jpg',
                        description='05_render/DESCRIPTION.md', credits='04_scene/assets/sound.md')
        if set(package['files']) != set(expected): return False
        for key, name in expected.items():
            record = package['files'][key]
            if record['path'] != name or record['sha256'] != _hash(project / name): return False
        description = (project / expected['description']).read_text()
        if package['disclosure'] != description or not re.search(r'^ai_label:\s*(true|false)\s*$', description, re.M): return False
        if any((project / '01_voice/takes').glob('*.json')):
            return bool(re.search(r'^ai_label:\s*true\s*$', description, re.M) and description.rstrip().endswith('Voice-over made with AI.'))
        return True
    except (OSError, ValueError, KeyError, TypeError): return False


def _approved(root, video_id, stage):
    from studio.workspace import WorkspaceError
    try:
        from studio.workspace import review_state
        state = review_state(root, video_id, stage)
        return state.get('state') in ('approved',) and state.get('ready') is True
    except (ValueError, KeyError, WorkspaceError): return False


def _save_run(path, run):
    atomic_json(path, run)
    root = path.parents[2]
    atomic_json(root / run['project_relative'] / 'runs' / run['id'] / 'run.json', run)


def run_video(root, video_id, settings=None, resume=None):
    from studio.project_paths import resolve_project, project_id
    from studio import workspace as ws
    root = Path(root).resolve()
    project = resolve_project(root, video_id)
    video_id = project_id(root, project)
    with production_lock(root, 'run:' + video_id):
        if resume:
            if not re.fullmatch(r'[a-f0-9]{32}', str(resume)): raise ValueError('Invalid run ID.')
            path = root / '.studio/runs' / (resume + '.json')
            run = json.loads(path.read_text())
            if run['video_id'] != video_id: raise ValueError('This run belongs to another project.')
            saved = validate_settings(run['settings'])
            if settings is not None and validate_settings(settings) != saved:
                raise ValueError('Resume uses its saved settings. Start a new run to change them.')
        else:
            if settings is None:
                candidate = project / 'run_settings.json'
                settings = json.loads(candidate.read_text()) if candidate.exists() else None
            saved = validate_settings(settings)
            ident = uuid.uuid4().hex
            path = root / '.studio/runs' / (ident + '.json')
            run = dict(id=ident, video_id=video_id, settings=saved, stages={}, builder_id='builder-' + ident,
                       status='running', repair_rounds=0)
        run['project_relative'] = str(project.relative_to(root))
        manifest = json.loads((project / 'project.json').read_text())
        if manifest.get('brand', 'videofactory') != saved['brand']: raise ValueError('Run brand differs from project brand.')
        for field in ('format', 'language'):
            if manifest.get(field) and manifest[field] != saved[field]: raise ValueError('Run ' + field + ' differs from project settings.')
        run['status'] = 'running'
        _save_run(path, run)
        upstream = {}
        invalidated = False
        for stage in STAGES:
            if stage == 'research' and not saved['research']: continue
            lessons = load_lessons(root, saved['brand'], stage)
            fingerprint = hashlib.sha256(json.dumps(dict(settings=saved, upstream=upstream, lessons=lessons,
                dependencies=_dependencies(root, project, saved['brand']),
                brand_hash=_hash(root / 'brands' / saved['brand'] / 'brand.md') if (root / 'brands' / saved['brand'] / 'brand.md').exists() else None), sort_keys=True).encode()).hexdigest()
            if stage in ws.GATES and stage != 'research' and ws._not_applicable(root, video_id, stage):
                run['stages'][stage] = dict(status='skipped', validation='not-applicable',
                                           input_fingerprint=fingerprint, artifacts={}, lessons=lessons)
                upstream[stage] = dict(validation='not-applicable', input_fingerprint=fingerprint)
                record_learning(project, run['id'], stage)
                _save_run(path, run)
                continue
            old = run['stages'].get(stage, {})
            try:
                current = _artifacts(project, stage)
                valid = _valid(project, stage)
                if stage == 'critic' and valid:
                    valid = critic_valid(project, json.loads((project / '05_render/critic.json').read_text()), run['builder_id'])
            except (OSError, ValueError, KeyError, TypeError):
                current, valid = {}, False
            reusable = (not invalidated and old.get('status') == 'validated' and
                        old.get('input_fingerprint') == fingerprint and old.get('artifacts') == current and valid)
            if (not reusable and not old and not invalidated and valid and
                    stage in ('research','brief','script','voice','transcript','cues','scene','render') and
                    _approved(root, video_id, stage)):
                run['stages'][stage] = dict(status='validated', input_fingerprint=fingerprint,
                                           artifacts=current, lessons=lessons, reused_review=True)
                record_learning(project, run['id'], stage)
                _save_run(path, run)
                reusable = True
            if not reusable:
                invalidated = True
                run['stages'][stage] = dict(status='running', input_fingerprint=fingerprint, lessons=lessons)
                _save_run(path, run)
                context = dict(run_id=run['id'], video_id=video_id, settings=saved, lessons=lessons,
                               builder_id=run['builder_id'])
                try:
                    if stage == 'critic':
                        while True:
                            stage_runner(root, project, stage, context)
                            report = json.loads((project / '05_render/critic.json').read_text())
                            if critic_valid(project, report, run['builder_id']): break
                            if run['repair_rounds'] >= 3: raise ValueError('Critic evidence failed after three repair rounds.')
                            if not report.get('audio_review', {}).get('listened'): raise ValueError('Actual audio review is missing.')
                            run['repair_rounds'] += 1
                            _save_run(path, run)
                            stage_runner(root, project, 'scene', dict(context, repair=report))
                            stage_runner(root, project, 'checks', context)
                            stage_runner(root, project, 'render', context)
                            if not all(_valid(project, repaired) for repaired in ('scene','checks','render')):
                                raise ValueError('Repair produced invalid scene, check or render evidence.')
                    else: stage_runner(root, project, stage, context)
                    if not _valid(project, stage): raise ValueError('Required stage artifacts are missing or invalid.')
                    run['stages'][stage].update(status='validated', artifacts=_artifacts(project, stage))
                    record_learning(project, run['id'], stage)
                except Exception as error:
                    run['stages'][stage].update(status='needs-attention', error=str(error))
                    run['status'] = 'needs-attention'
                    record_learning(project, run['id'], stage, [str(error)])
                    _save_run(path, run)
                    return run
                _save_run(path, run)
            upstream[stage] = _artifacts(project, stage)
            if (saved['review_mode'] == 'selected-stages' and stage in saved['selected_stages'] and
                    not _approved(root, video_id, stage)):
                run.update(status='waiting-for-review', review_stage=stage)
                _save_run(path, run)
                return run
        run.update(status='ready-for-final-review', review_stage='render')
        _save_run(path, run)
        return run
