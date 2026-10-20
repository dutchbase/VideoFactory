import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import anim


class UseClipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vdir = self.root / 'videos/demo'
        (self.vdir / '04_scene').mkdir(parents=True)
        (self.vdir / 'project.json').write_text('{"format": "wide"}')
        pack = self.root / 'brands/b/library/motion'
        pack.mkdir(parents=True)
        (pack / 'manifest.json').write_text(json.dumps({'assets': [
            {'id': 'AIM-05', 'type': 'scene', 'file': 'AIM-05.dc.html', 'defaultDuration': 6},
            {'id': 'CAP-01', 'type': 'overlay', 'file': 'CAP-01.dc.html', 'defaultDuration': 6}]}))
        p = patch.object(anim, 'ROOT', self.root); p.start(); self.addCleanup(p.stop)
        self.register = patch.object(anim, 'register_clip').start()
        self.run = patch.object(anim.subprocess, 'run').start()
        self.addCleanup(patch.stopall)

    def test_stock_video_becomes_frames(self):
        src = self.root / 'clip.mp4'
        src.write_bytes(b'x')
        anim._copy_clip(self.vdir)(src, 'bg', '0:02', '7.5')
        self.register.assert_called_once_with(self.vdir, src, 'bg', 2.0, 7.5, 12, 1280)

    def test_bad_range_stops(self):
        src = self.root / 'clip.mp4'
        src.write_bytes(b'x')
        for start, end in [('5', '2'), ('x', '3')]:
            with self.assertRaises(SystemExit):
                anim._copy_clip(self.vdir)(src, 'bg', start, end)
        self.register.assert_not_called()

    def test_motion_renders_once_and_registers(self):
        with patch('libcore.record_use') as log:
            anim._use_motion(self.vdir, 'motion:b/AIM-05', None, None, None)
        self.run.assert_called_once()
        self.assertIn('16:9', self.run.call_args.args[0])
        src = self.root / 'library/cache/motion/AIM-05_16x9_6s.mp4'
        self.register.assert_called_once_with(self.vdir, src, 'aim-05', 0.0, 6.0, 24, 1920)
        self.assertEqual(log.call_args.args[2], 'MIT')
        src.parent.mkdir(parents=True)
        src.write_bytes(b'x')
        self.run.reset_mock()
        with patch('libcore.record_use'):
            anim._use_motion(self.vdir, 'motion:b/AIM-05', 'scan', '1', '4')
        self.run.assert_not_called()
        self.assertEqual(self.register.call_args.args[2:], ('scan', 1.0, 4.0, 24, 1920))

    def test_motion_edited_page_renders_into_the_video(self):
        edited = self.vdir / '04_scene/motion/AIM-05.dc.html'
        edited.parent.mkdir(parents=True)
        edited.write_text('<html>own text</html>')
        with patch('libcore.record_use'):
            anim._use_motion(self.vdir, 'motion:b/AIM-05', None, None, None)
        args = self.run.call_args.args[0]
        self.assertEqual(args[args.index('--page') + 1], str(edited))
        self.assertEqual(args[args.index('--outDir') + 1], str(edited.parent))
        self.assertEqual(self.register.call_args.args[1], edited.parent / 'AIM-05_16x9_6s.mp4')

    def test_motion_tall_format_and_refusals(self):
        (self.vdir / 'project.json').write_text('{"format": "tall"}')
        with patch('libcore.record_use'):
            anim._use_motion(self.vdir, 'motion:b/AIM-05', None, None, None)
        self.assertIn('9:16', self.run.call_args.args[0])
        for ref in ['motion:b/CAP-01', 'motion:b/NOPE-1', 'motion:missing/AIM-05']:
            with self.assertRaises(SystemExit):
                anim._use_motion(self.vdir, ref, None, None, None)


if __name__ == '__main__':
    unittest.main()
