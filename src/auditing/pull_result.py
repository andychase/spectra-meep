import io
import pathlib
import sys
from tarfile import TarFile

from src.utils.db import get_s3_client


def main(uuid_id):
    out_dir = pathlib.Path(__file__).parent.parent / "out"
    out_dir.mkdir(parents=False, exist_ok=True)
    with open(out_dir / f"{uuid_id}.txt", "wb") as out_f:
        s3 = get_s3_client()
        f = io.BytesIO()
        s3.download_fileobj('spectrameep', uuid_id + ".tar.gz", f)
        f.seek(0)
        tar = TarFile.open(mode='r:gz', fileobj=f)
        listings = list(tar.getmembers())
        for listing in listings:
            if "LOGFILE_" in listing.name:
                file = tar.extractfile(listing)
                out_f.write(file.read())


if __name__ == "__main__":
    main(sys.argv[1])
