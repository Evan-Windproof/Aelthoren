"""Guard user-owned distribution configuration against accidental replacement."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import privacy


class DistributionPreservation(unittest.TestCase):
    def test_unmanaged_policy_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary)
            path = binary / 'distribution/policies.json'
            path.parent.mkdir()
            path.write_text('{"policies":{"UserMessaging":{"Locked":true}}}')
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                privacy.install_policies(binary)
            self.assertEqual(path.read_bytes(), original)

    def test_edited_managed_configuration_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary)
            privacy.install_policies(binary)
            ini = binary / 'distribution/distribution.ini'
            ini.write_text('owner-edited preferences')
            with self.assertRaises(ValueError):
                privacy.install_policies(binary)
            self.assertEqual(ini.read_text(), 'owner-edited preferences')

    def test_reviewed_update_requires_matching_previous_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / 'bin'
            repo = Path(temporary) / 'project'
            (repo / 'config').mkdir(parents=True)
            (repo / 'config/policy').write_text('first reviewed configuration')
            with mock.patch.object(privacy,'ROOT',repo):
                path = privacy.install_file(binary,'config/policy','policies.json')
                (repo / 'config/policy').write_text('second reviewed configuration')
                privacy.install_file(binary,'config/policy','policies.json')
            self.assertEqual(path.read_text(),'second reviewed configuration')


if __name__ == '__main__':
    unittest.main()
