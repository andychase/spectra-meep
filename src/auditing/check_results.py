from tarfile import TarFile

import tqdm

from src.utils.db import with_conn, get_s3_client
import io


def get_finished_uuids():
    result = []
    for cur in with_conn():
        cur.execute("""
            SELECT name, save_uuid
            from meepdb.chem c
            where is_done is TRUE
            order by name_length
        """)
        result = list(cur.fetchall())
    return result


def find_bad_mult():
    ids = get_finished_uuids()
    s3 = get_s3_client()
    for chem_name, uuid_id in tqdm.tqdm(ids):
        f = io.BytesIO()
        s3.download_fileobj('spectrameep', uuid_id + ".tar.gz", f)
        f.seek(0)
        tar = TarFile.open(mode='r:gz', fileobj=f)
        listings = list(tar.getmembers())
        for listing in listings:
            if "LOGFILE_" in listing.name:
                file = tar.extractfile(listing)
                contents = file.read().decode("ascii")
                if "ILLEGAL EXTENDED BASIS FUNCTION REQUESTED" in contents:
                    yield chem_name


def main():
    for cur in with_conn():
        for mult in find_bad_mult():
            print(f"Fixing {mult}")
            cur.execute("""
            update meepdb.chem 
            set is_done = FALSE
            where name = %s""", (mult,))


if __name__ == "__main__":
    main()
