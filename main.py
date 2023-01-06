import json
import logging
import pathlib
import sys
import time

from utils import run_gamess
from utils.inchi_to_gamess_format import inchi_to_gamess


def run_single(chem, _dir):
    ff_input = inchi_to_gamess(chem)
    completed_ok, punch_files, logfiles = run_gamess.run_with_input(ff_input, _dir)
    return completed_ok


def run_simulations(i):
    with open(pathlib.Path(__file__).parent / "data" / "ff_inputs_db.json") as f:
        ff_inputs_db = json.load(f)
        logfiles = []
        ff_inputs_db_sorted = sorted([(k, len(k), v) for k, v in ff_inputs_db.items()], key=lambda _: _[1])
        (chem, chem_len, ff_input) = ff_inputs_db_sorted[i]
        try:
            start_time = time.monotonic()
            _dir = pathlib.Path("/tmp/spectra_meep")
            completed_ok, punch_files, logfiles = run_gamess.run_with_input(ff_input, _dir)
            app = "" if completed_ok else "_failed"
            with open((pathlib.Path(__file__).parent / "data" / (str(i) + app)).with_suffix(".txt"), "w") as out_f:
                out_f.write("\n".join((chem, str(time.monotonic() - start_time), *logfiles)))
        except Exception:
            logging.exception("Exception thrown")
        else:
            print(f"{i} completed {'ok' if completed_ok else 'not ok'}")
        for log in logfiles:
            if "RAMAN" in log:
                open("LOG", "w").write(log)


if __name__ == "__main__":
    run_simulations(int(sys.argv[1]))

# Get reference spectra
# Generate Raman Spectra from Simulator
# Make machine learning model to convert simulated to reference
