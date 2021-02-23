#!/usr/bin/env python

"""
This is pytest for aiida_twinpy.common.kpoints.
"""

from copy import deepcopy
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import load_node, Bool, Dict, Str
from aiida.plugins import WorkflowFactory
from aiida.engine import submit
from twinpy.interfaces.aiida.base import get_aiida_structure


@with_dbenv()
def test_ShearWorkChain(env_parameters,
                        datetime_now,
                        test_group,
                        hcp_mg_relax_cell,
                        default_kpoints_conf,
                        default_shear_conf,
                        default_calculator_settings):
    """
    Check ShearWorkChain.
    """
    kpoints_conf = deepcopy(default_kpoints_conf)
    shear_conf = deepcopy(default_shear_conf)
    calculator_settings = deepcopy(default_calculator_settings)

    wf = WorkflowFactory('twinpy.shear')
    builder = wf.get_builder()
    builder.calculator_settings = Dict(dict=calculator_settings)
    builder.computer = Str(env_parameters['computer'])
    builder.dry_run = Bool(False)
    builder.structure = get_aiida_structure(cell=hcp_mg_relax_cell)
    builder.is_phonon = Bool(True)
    builder.shear_conf = Dict(dict=shear_conf)
    builder.use_kpoints_interval = Bool(True)
    builder.kpoints_conf = Dict(dict=kpoints_conf)
    builder.metadata.label = 'test ShearWorkChain (%s)' % datetime_now
    future = submit(builder)
    test_group.add_nodes(load_node(future.pk))
    print("")
    print("# ---------------------------------------------------------------")
    print("# pk {} is added to group: {}".format(future.pk, test_group.label))
    print("# ---------------------------------------------------------------")
