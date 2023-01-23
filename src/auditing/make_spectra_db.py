import json
import logging
import multiprocessing
import pathlib
from io import StringIO

from tqdm import tqdm

from auditing import pull_result
from utils.db import with_conn
from utils.process_logfile import simple_parse

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
    logfile.seek(0)
    try:
        data = simple_parse(logfile)
        return name, data
    except Exception:
        logging.exception("E")


def _main():
    pool = multiprocessing.Pool()
    output = {}
    for result in pool.imap_unordered(process, tqdm(get_completed()[:100]), chunksize=1):
        if result:
            name, data = result
            output[name] = data
    return output


def main():
    output_filename = pathlib.Path(__file__).parent.parent.parent / "data" / "activities.json"
    with open(output_filename, "w") as f:
        json.dump(dict(_main()), f)


if __name__ == "__main__":
    main()
