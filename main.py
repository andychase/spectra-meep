import json
import logging
import pathlib

import run_ff

if __name__ == "__main__":
    with open(pathlib.Path(__file__).parent / "ff_inputs_db.json") as f:
        ff_inputs_db = json.load(f)
        ff_inputs_db_sorted = sorted([(k, len(v), v) for k, v in ff_inputs_db.items()], key=lambda _: _[1])
        for i, ff_input in enumerate(ff_inputs_db_sorted):
            if not ff_input[0]:
                continue
            try:
                punch_files, logfiles = run_ff.run_with_input(ff_input[2])
                with open((pathlib.Path(__file__).parent / "data" / str(i)).with_suffix(".json"), "w") as out_f:
                    json.dump({
                        "chem": ff_input[0],
                        "log1": logfiles[0],
                        "log2": logfiles[1]
                    }, out_f)
            except:
                logging.exception("Exception thrown")


# Get reference spectra
# Generate Raman Spectra from Simulator
# Make machine learning model to convert simulated to reference
