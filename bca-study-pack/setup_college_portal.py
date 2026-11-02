"""Windows installer for the complete English BCA Semester III study portal."""
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

URL = (
    "https://raw.githubusercontent.com/iajyshharma/test-repo/"
    "58084b83be9a4cda7dfe2cc8778c701621f006de/"
    "bca-study-pack/BCA_Semester_3_Study_Pack.zip"
)
SHA256 = "4e5180499bd10ea918be0cb2f6bc03fa30750edf9fa33967d656b8219f61c7fd"


def prepare(package, desktop):
    if hashlib.sha256(package).hexdigest() != SHA256:
        raise ValueError("The downloaded package did not pass verification.")
    desktop = Path(desktop)
    desktop.mkdir(parents=True, exist_ok=True)
    project = desktop / "College-Study-Portal"
    number = 2
    while project.exists() or project.with_suffix(".zip").exists():
        project = desktop / f"College-Study-Portal-{number}"
        number += 1

    with tempfile.TemporaryDirectory() as temporary:
        extraction = Path(temporary).resolve()
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            for entry in archive.infolist():
                destination = (extraction / entry.filename).resolve()
                if not destination.is_relative_to(extraction):
                    raise ValueError("Invalid archive path.")
                if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Unexpected symbolic link in archive.")
            if archive.testzip() is not None:
                raise ValueError("Archive integrity check failed.")
            archive.extractall(extraction)
        source = extraction / "BCA-Semester-3-Study-Pack"
        shutil.copytree(source, project)
    project.with_suffix(".zip").write_bytes(package)
    return project


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError("Install Python 3.10 or newer first.")
    desktop = Path.home() / "Desktop"
    if os.name == "nt":
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as registry:
            desktop = Path(os.path.expandvars(winreg.QueryValueEx(registry, "Desktop")[0]))

    print("Downloading the verified English study pack...")
    with urllib.request.urlopen(URL, timeout=60) as response:
        package = response.read(2 * 1024 * 1024 + 1)
    project = prepare(package, desktop)
    print("Project created:", project)
    print("Open PDFs directly in:", project / "PDFs")

    options = {"creationflags": subprocess.CREATE_NEW_CONSOLE} if os.name == "nt" else {}
    environment = dict(os.environ, PORTAL_PORT="0", PORTAL_NO_BROWSER="0")
    subprocess.Popen(
        [sys.executable, "app.py", "--serve"],
        cwd=project, env=environment, **options
    )
    if os.name == "nt":
        try:
            os.startfile(str(project / "College-Study-Portal.code-workspace"))
        except OSError:
            print("Open the project folder in VS Code manually.")
    print("Keep the server terminal open while using the portal.")
    print("Next time, double-click START.bat inside the project folder.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Setup could not finish:", error)
        sys.exit(1)
