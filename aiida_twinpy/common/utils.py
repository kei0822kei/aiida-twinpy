#!usr/bin/env python

from aiida.engine import calcfunction
from aiida.orm import load_node, Dict, Float
from aiida.orm.nodes.data import StructureData
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from twinpy.structure import get_pymatgen_structure, HexagonalClosePacked

@calcfunction
def get_sheared_structures(structure, shear_conf):
    conf = dict(shear_conf)
    pmgstructure = structure.get_pymatgen_structure()
    a = pmgstructure.lattice.a
    c = pmgstructure.lattice.c
    specie = pmgstructure.species[0].symbol
    symmetry = SpacegroupAnalyzer(pmgstructure)
    wyckoff = symmetry.get_symmetry_dataset()['wyckoffs'][0]
    parent = HexagonalClosePacked(a, c, specie, wyckoff)
    parent.set_parent(twinmode=conf['twinmode'])
    ratios = [ i / (int(conf['grids'])-1) for i in range(int(conf['grids'])) ]
    strain = parent.shear_strain_function
    shears = []
    for ratio in ratios:
        shear = get_pymatgen_structure(
                    parent.get_sheared_structure(ratio=ratio),
                    structure_type=shear_conf['structure_type'])
        shears.append(shear)

    return_vals = {}
    return_vals['parent'] = StructureData(
            pymatgen_structure=shears[0])
    shear_settings = {'shear_ratios': ratios}
    return_vals['shear_settings'] = Dict(dict=shear_settings)
    return_vals['strain'] = Float(abs(strain(parent.r)))
    for i in range(len(ratios)):
        shear = StructureData(pymatgen_structure=shears[i])
        shear.label = 'shear_%03d' % i
        shear.description = 'shear_%03d' % i + \
                ' ' + shear_conf['structure_type']
        return_vals[shear.label] = shear
    return return_vals

@calcfunction
def collect_relax_results(**rlx_results):
    return_vals = {}
    energies = []
    for i in range(len(rlx_results)):
        label = 'shear_%03d' % i
        relax_label = 'rlx_' + label
        energies.append(
            rlx_results[relax_label]['total_energies']['energy_no_entropy'])
    return_vals['relax_results'] = Dict(dict={'energies': energies})
    return return_vals
