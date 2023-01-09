from openbabel import pybel
import os


# os.environ["BABEL_DATADIR"] = "C:\Program Files (x86)\OpenBabel-3.1.1\openbabel-3.1.1\data"

# Create an Open Babel molecule from an InChI string
def inchi_to_gamess(input_inchi):
    """
    >>> inchi_to_gamess('InChI=1S/H2/h1H')[:8]
    ' $CONTRL'
    """
    if input_inchi == "":
        return input_inchi
    molecule: pybel.Molecule = pybel.readstring('inchi', input_inchi)
    is_organic = any(a.atomicnum == 6 for a in molecule.atoms)
    if is_organic:
        molecule.make3D("gaff", steps=100)
    else:
        molecule.make3D("uff", steps=100)
    molecule.localopt()
    return molecule.write("inp")


if __name__ == "__main__":
    import sys

    print(inchi_to_gamess(sys.argv))
