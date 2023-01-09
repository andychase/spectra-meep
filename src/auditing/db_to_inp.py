import csv
import multiprocessing

from tqdm import tqdm

from utils.db import with_conn, get_s3_client
from utils.inchi_to_gamess_format import inchi_to_gamess


def target(i):
    return i, inchi_to_gamess(i)


def main():
    chems = []
    for conn in with_conn():
        conn.execute("""            SELECT name
                from meepdb.chem c            
                """)
        chems = [_[0] for _ in conn.fetchall()]

    with open("out.csv", "w", newline='') as f:
        c = csv.writer(f)
        for chem in tqdm(chems):
            try:
                result = target(chem)
                c.writerow([chem, result])
            except Exception as e:
                print(e.__class__)


if __name__ == "__main__":
    main()
