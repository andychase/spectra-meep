import csv
import pathlib
from pprint import pprint

import tqdm as tqdm

from utils.db import with_conn
import csv


def get_data():
    ref = csv.reader(open(pathlib.Path(__file__).parent.parent.parent.parent / "db" / "meta" / "combined_metadata.csv",
                          encoding="utf8"))
    ref = {_[4] for _ in ref}
    ref.remove('InChI')
    pub_chem = csv.reader(open(pathlib.Path(__file__).parent.parent.parent.parent / "db" / "meta" / "PubChem.csv"))
    pub_chem = {_[12] for _ in pub_chem if len(_) > 11}
    pub_chem.remove('inchi')
    return ref, pub_chem


def get_mapping(db_chems):
    ref, pub_chem = get_data()
    for chem in db_chems:
        if chem in ref and chem in pub_chem:
            yield 'both', chem
        elif chem in ref:
            yield 'ref', chem
        elif chem in pub_chem:
            yield 'pubc', chem
        else:
            yield 'none', chem


def main():
    for cur in with_conn():
        cur.execute("select name from meepdb.chem")
        db_chems = {row[0] for row in cur.fetchall()}
        mapping = list(get_mapping(db_chems))
        for i in range(0, len(db_chems), 1000):
            cur.executemany("""
            UPDATE meepdb.chem
            set source = %s
            where name = %s
            """, mapping[i:i + 1000])


if __name__ == "__main__":
    main()
