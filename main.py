import pathlib

import jcamp
import re
import csv

strip_re = re.compile(r'[^a-zA-Z0-9]')


def strip_non_alpha(text):
    return strip_re.sub(text, 'w')


db_cols = {k: i for i, k in enumerate(
    "DB	ID	Name	Raman Laser Wavelength nm	InChI	Raman Laser Power W	Density g cm-1	"
    "Substance Type	Substance Type 2	Substance Type 3	Substance Type 4	"
    "Classification	Classification 2	Classification 3	Classification 4".split("\t")
)}

ref_db_path = pathlib.Path(__file__).parent.parent / "db" / "meta" / "combined_metadata.csv"
with open(ref_db_path, encoding = "utf8") as ref_db_file:
    ref_db_rows = list(csv.reader(ref_db_file))

ref_db = {
    strip_non_alpha(row[db_cols['Name']]): row for row in ref_db_rows
}

# Generate database of complexity and smiles from reference database
# Generate Raman Spectra from Simulator
