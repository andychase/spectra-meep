import csv
import pathlib
import re
from functools import cache


db_path = pathlib.Path(__file__).parent.parent.parent / "db"
ref_db_path = db_path / "meta" / "combined_metadata.csv"

db_cols = {k: i for i, k in enumerate(
    "DB	ID	Name	Raman Laser Wavelength nm	InChI	Raman Laser Power W	Density g cm-1	"
    "Substance Type	Substance Type 2	Substance Type 3	Substance Type 4	"
    "Classification	Classification 2	Classification 3	Classification 4".split("\t")
)}

strip_re = re.compile(r'[^a-zA-Z0-9]+')


def _strip_non_alpha_and_lower(text):
    return strip_re.sub('', text).lower()


@cache
def get_ref_db():
    with open(ref_db_path, encoding="utf8") as ref_db_file:
        ref_db_rows = list(csv.reader(ref_db_file))[1:]

    ref_db = {
        _strip_non_alpha_and_lower(row[db_cols['Name']]): row for row in ref_db_rows
    }
    return ref_db


def get_file_by_chem_name(chem_name):
    ref_db = get_ref_db()
    db = ref_db[chem_name][db_cols['DB']]
    _id = ref_db[chem_name][db_cols['ID']]
    pathlib.Path(db_path / db.lower() / str(_id))

def generate_ff_inputs():
    from inchi_to_gamess_format import inchi_to_gamess
    import multiprocessing
    s = {}
    db = get_ref_db()
    chems = [item[db_cols['InChI']] for name, item in db.items()]
    with multiprocessing.Pool(4) as p:
        res = p.imap_unordered(inchi_to_gamess, chems)
        for chem, r in res:
            s[chem] = r
    import json
    json.dump(s, open("../../data/ff_inputs_db.json", "w"))
