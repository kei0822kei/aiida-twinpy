#!usr/bin/env python

from aiida.engine import calcfunction
from aiida.orm import Float, Dict


@calcfunction
def store_shear_ratios(twinboundary_shear_conf):
    shear_ratios = twinboundary_shear_conf['shear_strain_ratios']
    return_vals = {}
    for i, ratio in enumerate(shear_ratios):
        label = 'ratio_%03d' % (i+1)
        return_vals[label] = Float(ratio)
    return return_vals


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


@calcfunction
def reset_isif(calculator_settings, isif):
    settings = calculator_settings.get_dict()
    if isif.value == 7:
        settings['relax']['relax_conf']['volume'] = True
        settings['relax']['relax_conf']['positions'] = False
        settings['relax']['relax_conf']['shape'] = False
    elif isif.value == 2:
        settings['relax']['relax_conf']['volume'] = False
        settings['relax']['relax_conf']['positions'] = True
        settings['relax']['relax_conf']['shape'] = False
    else:
        raise RuntimeError("isif: {} is not supported".format(isif.value))

    return_vals = {}
    return_vals['calculator_settings'] = Dict(dict=settings)
    return return_vals
