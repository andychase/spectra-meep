from openbabel import pybel

# Create an Open Babel molecule from an InChI string
def inchi_to_gamess(input_inchi):
    """
    >>> inchi_to_gamess('1S/H2/h1H')

    """
    molecule:pybel.Molecule = pybel.readstring('inchi', input_inchi)
    molecule.OBMol.make3D()
    return molecule.write("gamess")
