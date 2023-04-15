import json
import logging
import multiprocessing
import pathlib
import shelve
from io import StringIO

from tqdm import tqdm

from auditing import pull_result
from utils.db import with_conn
from utils.process_logfile import produce_raman_spectrum_file

OUT_DIR = pathlib.Path(__file__).parent.parent / "out"
(OUT_DIR / "chems").mkdir(exist_ok=True)
(OUT_DIR / "logfiles").mkdir(exist_ok=True)

def get_completed():
    for conn in with_conn():
        conn.execute("""
        select name, save_uuid
        from meepdb.chem
        where is_done is true
        and completed_ok is true
        """)
        return list(conn.fetchall())


def process(_input):
    name, save_uuid = _input

    logfile = StringIO(pull_result.main(save_uuid))
    with open((OUT_DIR / "logfiles" / save_uuid).with_suffix(".txt"), "w") as f:
        logfile.seek(0)
        f.write(logfile.read())
    logfile.seek(0)
    try:
        data = produce_raman_spectrum_file(logfile)
        with open((OUT_DIR / "chems" / save_uuid).with_suffix(".csv"), "w") as f:
            data.seek(0)
            f.write(data.read())
    except Exception:
        logging.exception("E")


def _main():
    get_completed()
    pool = multiprocessing.Pool(processes=30)
    for _ in map(process, tqdm(get_completed())):
        pass


if __name__ == "__main__":
    _main()
