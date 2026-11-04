import configparser
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import run_aelthoren as launcher


class ProfileIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        obj = self.root / 'obj'
        (obj / 'dist/bin/browser').mkdir(parents=True)
        (obj / 'dist/bin/application.ini').write_text('[App]\nName=Firefox\nVendor=Mozilla\nID=upstream-fixture\nVersion=153.6.0\n[Gecko]\nMinVersion=153.6.0\nMaxVersion=153.6.0\n')
        for name, value in [('OBJECT', obj), ('PROFILE_ROOT', self.root / 'profiles')]:
            patch = mock.patch.object(launcher, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def test_profile_escape_rejected(self):
        with self.assertRaises(ValueError):
            launcher.prepare_profile('../firefox')

    def test_unmarked_user_data_preserved(self):
        p = launcher.PROFILE_ROOT / 'existing'
        p.mkdir(parents=True)
        (p / 'prefs.js').write_text('existing data')
        with self.assertRaises(ValueError):
            launcher.prepare_profile('existing')
        self.assertEqual((p / 'prefs.js').read_text(), 'existing data')

    def test_named_profiles_separate(self):
        first = launcher.prepare_profile('one')
        second = launcher.prepare_profile('two')
        (first / 'sentinel').write_text('one')
        self.assertNotEqual(first, second)
        self.assertFalse((second / 'sentinel').exists())
        self.assertTrue((second / '.aelthoren-profile').exists())

    def test_brand_runtime_keeps_native_guid_and_engine_version(self):
        with mock.patch.object(launcher, 'verify_overlay'):
            path = launcher.application_file()
        config = configparser.ConfigParser()
        config.read(path)
        self.assertEqual(config['App']['Name'], 'Aelthoren')
        self.assertEqual(config['App']['RemotingName'], 'aelthoren')
        self.assertEqual(config['App']['ID'], 'upstream-fixture')
        self.assertEqual(config['Gecko']['MinVersion'], '153.6.0')

    def test_passthrough_profile_override_rejected(self):
        with mock.patch.object(sys, 'argv', ['run_aelthoren.py', '--', '--profile=/tmp/firefox']), \
             mock.patch('sys.stderr'), mock.patch.object(launcher.subprocess, 'call') as call:
            with self.assertRaises(SystemExit):
                launcher.main()
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
