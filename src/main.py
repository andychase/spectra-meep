import pathlib
import time

from utils import run_gamess


def run_simulations(chem):
    from utils.inchi_to_gamess_format import inchi_to_gamess
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
