import pathlib
import shutil
import subprocess


def compress_and_clean_dir(_dir):
    gz_path = _dir.parent / "output.tar.gz"
    subprocess.check_call(["tar", "czf", gz_path, _dir])
    for _dirs in pathlib.Path("/tmp").glob("spectra*"):
        if _dirs.is_dir():
            shutil.rmtree(_dirs)
        else:
            _dirs.unlink(missing_ok=True)
    yield gz_path
    gz_path.unlink(missing_ok=True)
