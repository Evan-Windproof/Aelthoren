"""Portable-launcher data preservation and desktop URL/path handling."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PortableGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'Alpha space $dollar %percent "quote" \\slash `tick`'
        self.app.mkdir()
        for p in (ROOT / 'packaging/linux').iterdir():
            if p.is_file():shutil.copy2(p, self.app / p.name)
        self.env = dict(os.environ, XDG_DATA_HOME=str(self.root/'data'), AELTHOREN_QA_CAPTURE=str(self.root/'args'))

    def test_unmarked_profile_data_is_preserved(self):
        p = self.root/'data/aelthoren-alpha/profiles/default'
        p.mkdir(parents=True)
        (p/'prefs.js').write_text('owner data')
        result = subprocess.run([str(self.app/'aelthoren')],env=self.env,capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual((p/'prefs.js').read_text(),'owner data')

    def test_profile_escape_and_native_override_rejected(self):
        for arguments in [['--profile','../firefox'],['--','-app','foreign.ini'],['--','--profile=/tmp/firefox']]:
            result = subprocess.run([str(self.app/'aelthoren'),*arguments],env=self.env,capture_output=True)
            self.assertEqual(result.returncode,2)

    def test_symlinked_managed_profile_is_refused(self):
        data = self.root/'data';data.mkdir()
        (data/'aelthoren-alpha').symlink_to(self.root/'foreign',target_is_directory=True)
        result = subprocess.run([str(self.app/'aelthoren')],env=self.env,capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertFalse((self.root/'foreign').exists())

    def test_unowned_desktop_entry_is_preserved(self):
        target = self.root/'data/applications/org.aelthoren.Browser.Alpha.desktop'
        target.parent.mkdir(parents=True);target.write_text('Owner desktop entry')
        result = subprocess.run([sys.executable,str(self.app/'desktop-entry.py'),'install'],env=self.env,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(target.read_text(),'Owner desktop entry')

    def test_desktop_exec_relocation_and_literal_url(self):
        app = self.app/'aelthoren'
        app.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$AELTHOREN_QA_CAPTURE"\n')
        app.chmod(0o755)
        subprocess.run([sys.executable,str(self.app/'desktop-entry.py'),'install'],env=self.env,check=True,capture_output=True)
        target=self.root/'data/applications/org.aelthoren.Browser.Alpha.desktop'
        subprocess.run(['desktop-file-validate',str(target)],check=True,capture_output=True)
        url='https://example.invalid/path?q=a&other=$literal'
        launched=subprocess.run(['gio','launch',str(target),url],env=self.env,capture_output=True)
        self.assertEqual(launched.returncode,0,launched.stderr.decode())
        for _ in range(100):
            if (self.root/'args').exists():break
            time.sleep(.01)
        self.assertEqual((self.root/'args').read_text().splitlines(),[url])
        subprocess.run([sys.executable,str(self.app/'desktop-entry.py'),'remove'],env=self.env,check=True,capture_output=True)
        self.assertFalse(target.exists())


if __name__=='__main__':unittest.main()
