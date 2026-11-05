"""Install reviewed product policies without overwriting unmanaged configuration."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def install_file(binary, source, filename):
    data = (ROOT / source).read_bytes()
    destination = binary / "distribution" / filename
    marker = destination.parent / (".aelthoren-" + filename + "-sha256")
    expected = hashlib.sha256(data).hexdigest() + '\n'
    if destination.exists():
        installed = destination.read_bytes()
        if installed == data and marker.is_file() and marker.read_bytes() == expected.encode('ascii'):
            return destination
        if installed != data:
            old = hashlib.sha256(installed).hexdigest()
            if not marker.exists() or marker.read_text().strip() != old:
                raise ValueError('Unmanaged enterprise policies exist; preserve them for review')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.json.tmp')
    temporary.write_bytes(data)
    temporary.replace(destination)
    marker.write_text(expected)
    return destination


def install_policies(binary):
    policies = install_file(binary, "config/privacy-policies.json", "policies.json")
    install_file(binary, "config/distribution.ini", "distribution.ini")
    return policies
