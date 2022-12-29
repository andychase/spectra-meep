import json
import logging
import pathlib

import run_ff
import run_games
from to_gms import inchi_to_gamess


def run_simulations():
    with open(pathlib.Path(__file__).parent / "ff_inputs_db.json") as f:
        ff_inputs_db = json.load(f)
        ff_inputs_db_sorted = sorted([(k, len(v), v) for k, v in ff_inputs_db.items()], key=lambda _: _[1])
        for i, ff_input in enumerate(ff_inputs_db_sorted):
            if not ff_input[0]:
                continue
            try:
                failed, punch_files, logfiles = run_ff.run_with_input(ff_input[2])
                with open((pathlib.Path(__file__).parent / "data" / str(i)).with_suffix(".json"), "w") as out_f:
                    json.dump({
                        "chem": ff_input[0],
                        "log1": logfiles[0],
                        "log2": logfiles[1]
                    }, out_f)
            except:
                logging.exception("Exception thrown")
            for log in logfiles:
                if "RAMAN" in log:
                    open("LOG", "w").write(log)


if __name__ == "__main__":
    chems = """
InChI=1S/C10H18O/c1-9(2)7-4-5-10(9,3)8(11)6-7/h7-8,11H,4-6H2,1-3H3/t7-,8+,10+/m1/s1
InChI=1S/C15H30O8/c1-2-3-4-13(21)23-12-15(8-19,9-20)11-22-10-14(5-16,6-17)7-18/h16-20H,2-12H2,1H3
InChI=1S/2C6H8O7.2Fe/c2*7-3(8)1-6(13,5(11)12)2-4(9)10;;/h2*13H,1-2H2,(H,7,8)(H,9,10)(H,11,12);;/q;;+2;+3/p-5
InChI=1S/C4H4S2/c5-4-2-1-3-6-4/h1-3,5H
""".strip().split()
    import time
    a = time.monotonic()
    for i, chem in enumerate(chems):
        completed_ok, punch_files, logfiles = run_games.run_with_input(inchi_to_gamess(chem))
        app = "" if completed_ok else "_failed"
        with open((pathlib.Path(__file__).parent / "data" / (str(i) + app)).with_suffix(".txt"), "w") as out_f:
            out_f.write("\n".join((chem, *logfiles)))
    print(time.monotonic() - a)


# Get reference spectra
# Generate Raman Spectra from Simulator
# Make machine learning model to convert simulated to reference
