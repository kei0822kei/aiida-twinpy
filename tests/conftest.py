#!/usr/bin/env python

"""
This is pytest fixtures.
"""

import os
import pytest
from pymatgen.io.vasp.inputs import Poscar
from twinpy.interfaces.pymatgen import get_cell_from_pymatgen_structure
from twinpy.file_io import read_yaml
import aiida_twinpy


TEST_DIR = os.path.dirname(os.getcwd())
PARAMETERS = read_yaml(os.path.join(TEST_DIR, 'settings.yaml'))


@pytest.fixture(autouse=True, scope='session')
def hcp_mg_relax_cell() -> tuple:
    """
    HCP Mg relax cell, wyckoff='c'.
    """
    aiida_twinpy_dir = os.path.dirname(
           os.path.dirname(aiida_twinpy.__file__))
    filename = os.path.join(aiida_twinpy_dir,
                            'tests',
                            'data',
                            'HCP_Mg_relax.poscar')
    pos = Poscar.from_file(filename)
    cell = get_cell_from_pymatgen_structure(pos.structure)

    return cell


@pytest.fixture(autouse=True, scope='session')
def default_kpoints_conf() -> dict:
    """
    Default kpoints configuration.
    """
    kpoints_conf = {
            'interval': 0.15,
            'decimal_handling': 'round',
            'use_symmetry': True,
            }

    return kpoints_conf


@pytest.fixture(autouse=True, scope='session')
def default_calculator_settings() -> dict:
    """
    Default kpoints configuration.
    """
    return CALC_SETTINGS


CALC_SETTINGS = {
    'phonon': {
        'incar_settings': {
            'addgrid': True,
            'ediff': 1e-06,
            'encut': 300,
            'ialgo': 38,
            'ismear': 1,
            'kpar': 2,
            'lcharg': False,
            'lreal': False,
            'lwave': False,
            'npar': 4,
            'prec': 'Accurate',
            'sigma': 0.5
        },
        'kpoints': {
            'mesh': [
                7,
                7,
                6,
            ],
            'offset': [
                0.0,
                0.0,
                0.5
            ]
        },
        'options': {
            'max_wallclock_seconds': 3600000,
            'queue_name': PARAMETERS['queue_name'],
        },
        'phonon_conf': {
            'distance': 0.03,
            'mesh': [
                18,
                18,
                10
            ],
            'supercell_matrix': [
                2,
                2,
                2
            ],
            'symmetry_tolerance': 1e-05
        },
        'potential_family': PARAMETERS['potential_family'],
        'potential_mapping': {
            'Mg': 'Mg_pv'
        },
        'vasp_code': PARAMETERS['vasp_code'],
    },
    'relax': {
        'clean_workdir': True,
        'incar_settings': {
            'addgrid': True,
            'ediff': 1e-06,
            'encut': 300,
            'ialgo': 38,
            'ismear': 1,
            'lcharg': False,
            'lreal': False,
            'lwave': False,
            'npar': 4,
            'prec': 'Accurate',
            'sigma': 0.5
        },
        'kpoints': {
            'mesh': [
                17,
                17,
                10
            ],
            'offset': [
                0.0,
                0.0,
                0.5
            ]
        },
        'options': {
            'max_wallclock_seconds': 360000,
            'queue_name': PARAMETERS['queue_name']
        },
        'parser_settings': {
            'add_energies': True,
            'add_forces': True,
            'add_kpoints': True,
            'add_misc': True,
            'add_stress': True
        },
        'potential_family': PARAMETERS['potential_family'],
        'potential_mapping': {
            'Mg': 'Mg_pv'
        },
        'relax_conf': {
            'algo': 'rd',
            'convergence_absolute': False,
            'convergence_max_iterations': 3,
            'convergence_on': True,
            'convergence_positions': 1e-03,
            'convergence_shape_angles': 0.1,
            'convergence_shape_lengths': 0.1,
            'convergence_volume': 1e-03,
            'force_cutoff': 1e-04,
            'perform': True,
            'positions': True,
            'shape': False,
            'steps': 40,
            'volume': False
        },
        'vasp_code': PARAMETERS['vasp_code'],
    }
}
