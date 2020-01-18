from aiida.plugins import DataFactory
from twinpy.crystalmaker import get_pymatgen_structure


# def get_aiida_structuredata(structure):
#     pmgstructure = get_pymatgen_structure(structure)
#     elements = [ element.value for element in pmgstructure.species ]
#     aiidastructure = DataFactory('structure')(structure[0])
#     for symbol, position in zip(elements, structure[1]):
#         aiidastructure.append_atom(position=position, symbols=symbol)
#     return aiidastructure
