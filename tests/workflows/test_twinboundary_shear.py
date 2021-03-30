#!/usr/bin/env python

"""
This is pytest for aiida_twinpy.common.kpoints.
"""

from copy import deepcopy
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import load_node, Dict, Str
from aiida.plugins import WorkflowFactory
from aiida.engine import submit


@with_dbenv()
def test_TwinBoundaryShearWorkChain(env_parameters,
                                    datetime_now,
                                    test_group,
                                    default_twinboundary_shear_settings,
                                    ):
    """
    Check TwinBoundaryRelaxWorkChain.
    """
    tb_shr_settings = deepcopy(default_twinboundary_shear_settings)
    tb_rlx_pk, addi_rlx_pks, tb_shr_conf = tb_shr_settings
    tb_rlx_structure = load_node(tb_rlx_pk).outputs.final_structure
    addi_rlx_structures = [ load_node(pk).outputs.relax__structure for pk in addi_rlx_pks ]

    wf = WorkflowFactory('twinpy.twinboundary_shear')
    builder = wf.get_builder()
    builder.computer = Str(env_parameters['computer'])
    builder.twinboundary_relax_structure = tb_rlx_structure
    builder.twinboundary_shear_conf = Dict(dict=tb_shr_conf)
    addi_rlx = AttributeDict()
    for i, structure in enumerate(addi_rlx_structures):
        addi_rlx.__setattr__('structure_%02d' % (i+1), structure)
    builder.additional_relax = addi_rlx
    builder.metadata.label = \
            'test TwinBoundaryShearWorkChain (%s)' % datetime_now
    future = submit(builder)
    test_group.add_nodes(load_node(future.pk))
    print("")
    print("# ---------------------------------------------------------------")
    print("# pk {} is added to group: {}".format(future.pk, test_group.label))
    print("# ---------------------------------------------------------------")
