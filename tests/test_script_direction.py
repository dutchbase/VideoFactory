import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import anim
from studio.workspace import gate_fingerprint, review_state, mark_ready, decide_review
from studio.jobs import build_argv


class ScriptDirectionTests(unittest.TestCase):
    def test_direction_is_reviewed_and_edits_invalidate_paid_voice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stage = root / 'videos/videofactory/demo/01_voice'
            stage.mkdir(parents=True)
            (stage.parent / "project.json").write_text(json.dumps({"brand": "videofactory"}))
            template = Path(anim.__file__).parent / '_templates/video/01_voice/brief.md'
            text = template.read_text()
            for label, value in {'Type': 'course', 'Language': 'en', 'Audience': 'new users', 'One outcome': 'save a draft'}.items():
                import re
                text = re.sub(rf'(?m)^- {label}:.*$', f'- {label}: {value}', text)
            (stage / 'brief.md').write_text(text)
            state = review_state(root, 'videofactory/demo', 'brief')
            self.assertIn('Selected opening', state['missing'])
            for label in ('Purpose', 'Evidence and uncertainties', 'Opening angle 1', 'Opening angle 2', 'Opening angle 3',
                          'Framework and reason', 'Selected opening', 'Beat outline', 'Promised payoff', 'Essential visual support'):
                text = text.replace(f'- {label}:\n', f'- {label}: reviewable direction for {label}\n')
            (stage / 'brief.md').write_text(text)
            (stage / 'script.md').write_text('```\nSave the draft, then check its name.\n```')
            for gate in ('brief', 'script'):
                fp = gate_fingerprint(root, 'videofactory/demo', gate)
                mark_ready(root, 'videofactory/demo', gate, fp)
                decide_review(root, 'videofactory/demo', gate, 'approved', 'Reviewer', 'approved in test', fp)
            fp = gate_fingerprint(root, 'videofactory/demo', 'script')
            with patch.object(anim, 'ROOT', root):
                anim.require_script_confirmation(stage.parent, fp)
                with self.assertRaises(SystemExit):
                    anim.require_script_confirmation(stage.parent, None)
                (stage / 'brief.md').write_text(text.replace('Promised payoff:', 'Promised payoff: changed'))
                self.assertEqual(review_state(root, 'videofactory/demo', 'script')['state'], 'stale')
                with self.assertRaises(SystemExit):
                    anim.require_script_confirmation(stage.parent, fp)

    def test_studio_passes_existing_confirmation_to_cli(self):
        fp = 'a' * 64
        args = build_argv(Path(anim.__file__).parent, 'voice-test', 'videofactory/demo', {'confirmation_fingerprint': fp})
        self.assertEqual(args[-2:], ['--confirm-script', fp])
