import io
import pathlib
import sys
from tarfile import TarFile

from src.utils.db import get_s3_client


def main(uuid_id):
    out_dir = pathlib.Path(__file__).parent.parent / "out"
    out_dir.mkdir(parents=False, exist_ok=True)
    s3 = get_s3_client()
    f = io.BytesIO()
    s3.download_fileobj('spectrameep', uuid_id + ".tar.gz", f)
    f.seek(0)
    tar = TarFile.open(mode='r:gz', fileobj=f)
    listings = list(listing for listing in tar.getmembers() if "LOGFILE_" in listing.name)
    listings.sort(key=lambda _: _.mtime, reverse=True)
    file = tar.extractfile(listings[0])
    return file.read().decode("utf-8")


if __name__ == "__main__":
    print(main(sys.argv[1]))
