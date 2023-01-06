import pathlib
import time

from utils import run_gamess
from utils.inchi_to_gamess_format import inchi_to_gamess


def run_single(chem, _dir):
    ff_input = inchi_to_gamess(chem)
    completed_ok, punch_files, logfiles = run_gamess.run_with_input(ff_input, _dir)
    exit(0 if completed_ok else 1)


def run_simulations(chem):
    start_time = time.monotonic()
    _dir = pathlib.Path("/tmp/spectra_meep")
    ff_input = inchi_to_gamess(chem)
    completed_ok, punch_files, logfiles = run_gamess.run_with_input(ff_input, _dir)
    app = "" if completed_ok else "_failed"
    print("\n".join((chem, str(time.monotonic() - start_time), *logfiles)))
    for log in logfiles:
        if "RAMAN" in log:
            open("LOG", "w").write(log)
    if completed_ok:
        print("completed ok")
    else:
        print("failed to complete")


if __name__ == "__main__":
    run_simulations("InChI=1S/N2O/c1-2-3")

# Get reference spectra
# Generate Raman Spectra from Simulator
# Make machine learning model to convert simulated to reference
