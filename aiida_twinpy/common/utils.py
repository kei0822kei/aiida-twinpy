#!usr/bin/env python

from aiida.engine import calcfunction
from aiida.orm import Dict, Node, QueryBuilder
from aiida.cmdline.utils.decorators import with_dbenv


@calcfunction
def collect_relax_results(**rlx_results):
    return_vals = {}
    energies = []
    for i in range(len(rlx_results)):
        label = 'shear_%03d' % i
        relax_label = 'rlx_' + label
        energies.append(
            rlx_results[relax_label]['total_energies']['energy_extrapolated'])
    return_vals['relax_results'] = Dict(dict={'energies': energies})
    return return_vals


@calcfunction
def collect_vasp_results(**vasp_results):
    return_vals = {}
    energies = []
    for i in range(len(vasp_results)):
        label = 'twinboundary_%03d' % i
        vasp_label = 'vasp_' + label
        energies.append(
            vasp_results[vasp_label]['total_energies']['energy_no_entropy'])
    return_vals['vasp_results'] = Dict(dict={'energies': energies})
    return return_vals


@calcfunction
def collect_twinboundary_shear_results(**rlx_results):
    return_vals = {}
    energies = []
    for i in range(len(rlx_results)):
        label = 'twinboundaryshear_%03d' % i
        relax_label = 'rlx_' + label
        energies.append(
            rlx_results[relax_label]['total_energies']['energy_no_entropy'])
    return_vals['relax_results'] = Dict(dict={'energies': energies})
    return return_vals


@calcfunction
def collect_modulation_results(**vasp_results):
    return_vals = {}
    energies = []
    for i in range(len(vasp_results)):
        label = 'modulation_%03d' % i
        vasp_label = 'vasp_' + label
        energies.append(
            vasp_results[vasp_label]['total_energies']['energy_no_entropy'])
    return_vals['vasp_results'] = Dict(dict={'energies': energies})
    return return_vals


@with_dbenv()
def get_create_node(pk, create_node_type):
    qb = QueryBuilder()
    qb.append(Node,
              filters={'id': pk}, tag='query')
    qb.append(create_node_type, with_outgoing='query')
    data = qb.all()
    assert len(data) == 1, \
            "Data creation node could not be detected for pk:{}.".format(pk)
    return data[0][0]


@with_dbenv()
def get_called_nodes(pk, called_node_type) -> list:
    """
    Get workflow pks in the node.

    Args:
        pk: Parent pk.
        called_node_type: Called node type.

    Returns:
        list: PKs.
    """
    qb = QueryBuilder()
    qb.append(Node, filters={'id':{'==': pk}}, tag='query')
    qb.append(called_node_type, with_incoming='query', project=['id'])
    pks = [ wf[0] for wf in qb.all() ]
    pks.sort(key=lambda x: x)
    return pks
