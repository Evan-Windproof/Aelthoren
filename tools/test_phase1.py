import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import prepare_phase1 as preparation


class PinnedInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'artifact'
        self.path.write_bytes(b'good')
        self.pin = {'size': 4, 'sha256': hashlib.sha256(b'good').hexdigest()}

    def test_accepts_matching_size_and_digest(self):
        preparation.verify(self.path, self.pin)

    def test_same_size_corruption_rejected(self):
        self.path.write_bytes(b'evil')
        with self.assertRaises(ValueError):
            preparation.verify(self.path, self.pin)

    def test_wrong_size_rejected(self):
        self.path.write_bytes(b'good plus extra')
        with self.assertRaises(ValueError):
            preparation.verify(self.path, self.pin)

    def test_wrong_source_revision_rejected_without_reset(self):
        with mock.patch.object(preparation.subprocess, 'check_output', return_value='0' * 40), \
             mock.patch.object(preparation.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                preparation.verify_source()
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
