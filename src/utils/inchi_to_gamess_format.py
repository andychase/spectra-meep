from openbabel import pybel
import os


# Create an Open Babel molecule from an InChI string
def inchi_to_gamess(input_inchi):
    """
    >>> inchi_to_gamess('InChI=1S/H2/h1H')[:8]
    ' $CONTRL'
    """
    if input_inchi == "":
        return input_inchi, ""
    molecule: pybel.Molecule = pybel.readstring('inchi', input_inchi)
    molecule.make3D()
    return molecule.write("inp")


if __name__ == "__main__":
    import sys

    print(inchi_to_gamess(sys.argv))
