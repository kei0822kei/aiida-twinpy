#!/usr/bin/env python

"""
This is pytest for aiida_twinpy.common.kpoints.
"""

from copy import deepcopy
import numpy as np
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm import Dict, Bool
from twinpy.interfaces.aiida.base import get_aiida_structure
from aiida_twinpy.common.kpoints import fix_kpoints


@with_dbenv()
def test_fix_kpoints(hcp_mg_relax_cell,
                     default_kpoints_conf,
                     default_calculator_settings):
    """
    Check fix_kpoints.
    """
    kpoints_conf = deepcopy(default_kpoints_conf)
    calculator_settings = deepcopy(default_calculator_settings)
    calculator_settings['phonon']['kpoints'] \
            = calculator_settings['relax']['kpoints']
    inputs = {
            'calculator_settings': Dict(dict=calculator_settings),
            'structure': get_aiida_structure(cell=hcp_mg_relax_cell),
            'kpoints_conf': Dict(dict=kpoints_conf),
            'is_phonon': Bool(True),
            }
    return_vals = fix_kpoints(**inputs)
    kpoints = return_vals['calculator_settings']['phonon']['kpoints']
    kpoints_expected = {'mesh': [9, 9, 4], 'offset': [0., 0., 0.5]}
    assert kpoints['mesh'] == kpoints_expected['mesh']
    np.testing.assert_allclose(kpoints['offset'], kpoints_expected['offset'])
