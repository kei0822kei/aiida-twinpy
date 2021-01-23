#!usr/bin/env python

import numpy as np
from aiida.engine import calcfunction
from aiida.orm import Dict, Float, Int, KpointsData, StructureData, load_node
from aiida_twinpy.common.interfaces import get_phonon_from_aiida
from aiida_phonopy.common.utils import phonopy_atoms_to_structure
from twinpy.api_twinpy import get_twinpy_from_cell
from twinpy.interfaces.aiida.base import (get_aiida_structure,
                                          get_cell_from_aiida)
from twinpy.interfaces.aiida.vasp import AiidaRelaxWorkChain
from twinpy.interfaces.aiida.twinboundary \
        import AiidaTwinBoudnaryRelaxWorkChain
from twinpy.structure.standardize import StandardizeCell


@calcfunction
def get_shear_structures(structure:StructureData,
                         shear_conf:Dict):
    """
    Get shear structure.

    Args:
        structure (StructureData): aiida structure data
        shear_conf (Dict): shear config

    Examples:
        Example of shear_conf

        >>> shear_conf = Dict(dict={
        >>>     'twinmode': '10-12',
        >>>     'grids': 5,
        >>>     })

        >>> # following settings are automatically set
        >>> dim = [1, 1, 1]
        >>> xshift = 0.
        >>> yshift = 0.
        >>> is_primitive = True
        >>> to_primitive = True
        >>> get_lattice = False
        >>> move_atoms_into_unitcell = True
        >>> no_idealize = False
        >>> symprec = 1e-5
        >>> no_sort = True
        >>> get_sort_list = False

    Note:
        When structure_type in_shear_conf is 'primitive' or 'conventional',
        create primitive or conventional standardized structure.
        The other case use 'base' structure which is original
        Twinpy output structure.
        The key structure_type and is_primitive are set 'primitive' and True
        automatically  because 'conventional' setting may changes
        the number of atoms which is difficult to deal with
        in the following process. Moreover, 'dim', 'xshift' and 'yshift'
        are set [1,1,1], 0. and 0. automatically.
    """
    dim = [1, 1, 1]
    xshift = 0.
    yshift = 0.
    is_primitive = True
    to_primitive = True
    get_lattice = False
    move_atoms_into_unitcell = True
    no_idealize = False
    symprec = 1e-5
    no_sort = True
    get_sort_list = False

    conf = dict(shear_conf)
    cell = get_cell_from_aiida(structure=structure,
                               get_scaled_positions=True)
    ratios = [ i / (int(conf['grids'])-1) for i in range(int(conf['grids'])) ]

    shear_structures = []
    vasp_input_structures = []
    for ratio in ratios:
        twinpy = get_twinpy_from_cell(cell=cell,
                                      twinmode=conf['twinmode'])
        twinpy.set_shear(
                xshift=xshift,
                yshift=yshift,
                dim=dim,
                shear_strain_ratio=ratio,
                is_primitive=is_primitive,
                )
        std = twinpy.get_shear_standardize(
                get_lattice=get_lattice,
                move_atoms_into_unitcell=move_atoms_into_unitcell,
                )
        shear_std_cell = std.get_standardized_cell(
                to_primitive=to_primitive,
                no_idealize=no_idealize,
                symprec=symprec,
                no_sort=no_sort,
                get_sort_list=get_sort_list,
                )
        shear_structures.append(get_aiida_structure(cell=std.cell))
        vasp_input_structures.append(get_aiida_structure(cell=shear_std_cell))

    return_vals = {
            'shear_settings': Dict(dict={'shear_ratios': ratios}),
            'gamma': Float(twinpy._shear.get_gamma()),
            'total_structures': Int(len(ratios)),
            }

    for i in range(len(ratios)):
        shear_structure = shear_structures[i]
        shear_structure.label = 'shear_orig_%03d' % i
        shear_structure.description = 'shear_orig_%03d' % i \
                                          + ' ratio: {}'.format(ratios[i])
        vasp_input_structure = vasp_input_structures[i]
        vasp_input_structure.label = 'shear_%03d' % i
        vasp_input_structure.description = 'shear_%03d' % i \
                                          + ' ratio: {}'.format(ratios[i])
        return_vals[vasp_input_structure.label] = vasp_input_structure
        return_vals[shear_structure.label] = shear_structure

    return return_vals


@calcfunction
def get_twinboundary_structure(structure, twinboundary_conf):
    """
    Get twinboudary structure.

    Args:
        structure (StructureData): aiida structure data
        twinboundary_conf (Dict): shear config

    Examples:
        Example of twinboundary_conf.

        >>> twinboundary_conf = Dict(dict={
        >>>     'twinmode': '10-12',
        >>>     'twintype': 1,
        >>>     'layers': 9,
        >>>     'delta': 0.06,
        >>>     'xshift': 0.,
        >>>     'yshift': 0.,
        >>>     'shear_strain_ratio': 0.,
        >>>     })

        >>> # following settings are automatically set
        >>> get_lattice = False
        >>> move_atoms_into_unitcell = True
        >>> to_primitive = True
        >>> no_idealize = False
        >>> symprec = 1e-5
        >>> no_sort = True
        >>> get_sort_list = False
    """
    get_lattice = False
    move_atoms_into_unitcell = True
    to_primitive = True
    no_idealize = False
    symprec = 1e-5
    no_sort = True
    get_sort_list = False

    parameters = {
        'get_lattice': get_lattice,
        'move_atoms_into_unitcell': move_atoms_into_unitcell,
        'to_primitive': to_primitive,
        'no_idealize': no_idealize,
        'symprec': symprec,
        'no_sort': no_sort,
        'get_sort_list': get_sort_list,
        }
    parameters.update(twinboundary_conf.get_dict())

    conf = dict(twinboundary_conf)
    cell = get_cell_from_aiida(structure=structure,
                               get_scaled_positions=True)
    twinpy = get_twinpy_from_cell(cell=cell,
                                  twinmode=conf['twinmode'])
    twinpy.set_twinboundary(twintype=conf['twintype'],
                            xshift=conf['xshift'],
                            yshift=conf['yshift'],
                            layers=conf['layers'],
                            delta=conf['delta'],
                            shear_strain_ratio=conf['shear_strain_ratio'],
                            )
    std = twinpy.get_twinboundary_standardize(
            get_lattice=get_lattice,
            move_atoms_into_unitcell=move_atoms_into_unitcell,
            )
    twinboundary_std_cell = std.get_standardized_cell(
            to_primitive=to_primitive,
            no_idealize=no_idealize,
            symprec=symprec,
            no_sort=no_sort,
            get_sort_list=get_sort_list,
            )
    twinboundary_structure = get_aiida_structure(cell=std.cell)
    twinboundary_structure.label = 'twinboundary_orig'
    twinboundary_structure.description = \
            'twinboundary not standardized original structure'
    vasp_input_structure = get_aiida_structure(cell=twinboundary_std_cell)
    vasp_input_structure.label = 'twinboundary'
    vasp_input_structure.description = \
            'twinboundary standardized structure'

    return_vals = {}
    return_vals['parameters'] = Dict(dict=parameters)
    return_vals[twinboundary_structure.label] = twinboundary_structure
    return_vals[vasp_input_structure.label] = vasp_input_structure

    return return_vals


@calcfunction
def get_twinboundary_shear_structure(twinboundary_shear_conf,
                                     shear_strain_ratio,
                                     previous_relax_pk,
                                     previous_shear_strain_ratio=None,
                                     previous_original_structure=None):
    """
    If latest_structure is None, use s=0 structure as the original
    structure to be sheared.
    """
    conf = twinboundary_shear_conf.get_dict()
    aiida_twinboundary_relax = AiidaTwinBoudnaryRelaxWorkChain(
            load_node(conf['twinboundary_relax_pk']))
    aiida_relax_collection = aiida_twinboundary_relax.get_aiida_relax(
            additional_relax_pks=conf['additional_relax_pks'])
    twinboundary_analyzer = aiida_twinboundary_relax.get_twinboundary_analyzer(
            additional_relax_pks=conf['additional_relax_pks'])

    if previous_shear_strain_ratio is None:
        orig_cell = twinboundary_analyzer.get_shear_cell(
                shear_strain_ratio=shear_strain_ratio.value,
                is_standardize=False)
        cell = twinboundary_analyzer.get_shear_cell(
            shear_strain_ratio=shear_strain_ratio.value,
            is_standardize=True)

    else:
        previous_original_cell = get_cell_from_aiida(
                previous_original_structure)
        previous_aiida_relax = AiidaRelaxWorkChain(
                load_node(previous_relax_pk.value))
        previous_relax_analyzer = previous_aiida_relax.get_relax_analyzer(
                original_cell=previous_original_cell)
        atom_positions = \
                previous_relax_analyzer.final_cell_in_original_frame[1]
        orig_cell = twinboundary_analyzer.get_shear_cell(
                shear_strain_ratio=shear_strain_ratio.value,
                is_standardize=False,
                atom_positions=atom_positions)
        cell = twinboundary_analyzer.get_shear_cell(
            shear_strain_ratio=shear_strain_ratio.value,
            is_standardize=True,
            # is_standardize=False,
            atom_positions=atom_positions)

    orig_structure = get_aiida_structure(cell=orig_cell)
    structure = get_aiida_structure(cell=cell)

    # kpoints
    kpt_info = aiida_relax_collection.aiida_relaxes[0].get_kpoints_info()
    rlx_mesh = np.array(kpt_info['mesh'])
    rlx_offset = np.array(kpt_info['offset'])
    rlx_kpoints = (rlx_mesh, rlx_offset)
    std_base = StandardizeCell(twinboundary_analyzer.relax_analyzer.original_cell)
    orig_kpoints = std_base.convert_kpoints(kpoints=rlx_kpoints,
                                            kpoints_type='primitive')['original']
    std = StandardizeCell(orig_cell)
    kpoints = std.convert_kpoints(kpoints=orig_kpoints,
                                  kpoints_type='original')['primitive']
    kpt_orig = KpointsData()
    kpt_orig.set_kpoints_mesh(orig_kpoints[0], offset=orig_kpoints[1])
    kpt = KpointsData()
    kpt.set_kpoints_mesh(kpoints[0], offset=kpoints[1])

    return_vals = {}
    return_vals['twinboundary_shear_structure_orig'] = orig_structure
    return_vals['twinboundary_shear_structure'] = structure
    return_vals['kpoints_orig'] = kpt_orig
    return_vals['kpoints'] = kpt

    return return_vals


@calcfunction
def get_modulation_structures(modulation_conf):
    conf = modulation_conf.get_dict()
    phonon = get_phonon_from_aiida(conf['phonon_pk'])
    freq = []
    for phonon_mode in conf['phonon_modes']:
        freq.append(phonon.get_frequencies(phonon_mode[0]).tolist())

    unitcell = phonon.get_unitcell().cell
    primitive = phonon.get_primitive().cell
    u2p = np.round(np.dot(np.linalg.inv(primitive.T), unitcell.T)).astype(int)
    dimension = np.dot(u2p, conf['dimension'])
    phonon.set_modulations(dimension=dimension,
                           phonon_modes=conf['phonon_modes'])
    modulations = phonon.get_modulated_supercells()

    return_vals = {}
    return_vals['frequencies'] = Dict(dict={'frequencies': freq})
    for i, supercell in enumerate(modulations):
        modulation = phonopy_atoms_to_structure(supercell)
        modulation.label = 'modulation_%03d' % (i+1)
        modulation.description = 'modulation_%03d' % (i+1)
        return_vals[modulation.label] = modulation
    return return_vals
