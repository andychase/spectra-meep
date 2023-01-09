import csv
import pathlib

import tqdm as tqdm

from utils.db import with_conn

with open(pathlib.Path(__file__).parent.parent.parent / "data" / "inchi_to_gms.csv") as f:
    r = csv.reader(f)
    data = {k: v for k, v in (eval(_[1]) for _ in r)}

for cur in with_conn():
    datas = list(data.items())
    for i in tqdm.tqdm(range(0, len(data), 100), total=len(data)/100):
        cur.executemany("""
            UPDATE meepdb.chem c
            set gms_input = %s
            where name = %s
            """, ((gms, name) for name, gms in datas[i:i+100]))
