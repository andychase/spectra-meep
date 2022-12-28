import pathlib
import joblib

cache = joblib.Memory(location="cache")

# Generate database of complexity and smiles from reference database


def generate_filename_db():
    ref_path = pathlib.Path(__file__).parent / "db" / "raman"
    for _dir in reference.glob("*"):
        pass

# Generate Raman Spectra from Simulator
