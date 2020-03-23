#!/usr/bin/env python

from aiida.engine import calcfunction
from aiida.orm import Dict
from aiida.orm.nodes.data import StructureData
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from twinpy.structure import get_pymatgen_structure, HexagonalClosePacked

@calcfunction
def get_sheared_structures(structure, twinmode, grids):
    pmgstructure = structure.get_pymatgen_structure()
    a = pmgstructure.lattice.a
    c = pmgstructure.lattice.c
    specie = pmgstructure.species[0].symbol
    symmetry = SpacegroupAnalyzer(pmgstructure)
    wyckoff = symmetry.get_symmetry_dataset()['wyckoffs'][0]
    parent = HexagonalClosePacked(a, c, specie, wyckoff)
    parent.set_parent(twinmode=twinmode.value)
    ratios = [ i / (int(grids)-1) for i in range(int(grids)) ]
    shears = [ get_pymatgen_structure(
                   parent.get_sheared_structure(ratio=ratio))
               for ratio in ratios ]

    return_vals = {}
    return_vals['parent'] = StructureData(
            pymatgen_structure=get_pymatgen_structure(parent))
    shear_settings = {'shear_ratios': ratios}
    return_vals['shear_settings'] = Dict(dict=shear_settings)
    for i in range(len(ratios)):
        shear = StructureData(pymatgen_structure=shears[i])
        shear.label = 'shear_%03d' % (i+1)
        return_vals[shear.label] = shear
    return return_vals
