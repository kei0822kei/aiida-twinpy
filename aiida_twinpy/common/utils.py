#!usr/bin/env python

from aiida.engine import calcfunction
from aiida.orm import Dict

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

@calcfunction
def collect_vasp_results(**stc_results):
    return_vals = {}
    energies = []
    for i in range(len(stc_results)):
        label = 'vasp_%03d' % i
        relax_label = 'vasp_' + label
        energies.append(
            stc_results[relax_label]['total_energies']['energy_no_entropy'])
    return_vals['vasp_results'] = Dict(dict={'energies': energies})
    return return_vals
