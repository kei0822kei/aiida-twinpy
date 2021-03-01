#!/usr/bin/env python

"""
This is pytest for aiida_twinpy.common.kpoints.
"""

from copy import deepcopy
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm import load_node, Dict, Str
from aiida.plugins import WorkflowFactory
from aiida.engine import submit


@with_dbenv()
def test_TwinBoundaryShearWorkChain(env_parameters,
                                    datetime_now,
                                    test_group,
                                    default_twinboundary_shear_conf,
                                    ):
    """
    Check TwinBoundaryRelaxWorkChain.
    """
    twinboundary_shear_conf = deepcopy(default_twinboundary_shear_conf)
    wf = WorkflowFactory('twinpy.twinboundary_shear')
    builder = wf.get_builder()
    builder.computer = Str(env_parameters['computer'])
    builder.twinboundary_shear_conf = Dict(dict=twinboundary_shear_conf)
    builder.metadata.label = 'test TwinBoundaryRelaxWorkChain (%s)' % datetime_now
    future = submit(builder)
    test_group.add_nodes(load_node(future.pk))
    print("")
    print("# ---------------------------------------------------------------")
    print("# pk {} is added to group: {}".format(future.pk, test_group.label))
    print("# ---------------------------------------------------------------")
