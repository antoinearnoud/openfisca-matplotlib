# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import datetime

from openfisca_core import periods
from openfisca_france.reforms import inversion_revenus
from openfisca_france.tests.base import assert_near, tax_benefit_system

from matplotlib import pyplot


def brut_plot(revenu, count = 11, max_revenu = 5000, min_revenu = 0):
    year = 2014
    period = periods.period("{}-01".format(year))
    if revenu == 'chomage':
        brut_name = 'chobrut'
        imposable_name = 'cho'
        inversible_name = 'choi'
    elif revenu == 'retraite':
        brut_name = 'rstbrut'
        imposable_name = 'rst'
        inversible_name = 'rsti'
    elif revenu == 'salaire':
        brut_name = 'salaire_de_base'
        imposable_name = 'sal'
        inversible_name = 'sali'
    else:
        return

    single_entity_kwargs = dict(
        axes = [dict(count = count, max = max_revenu, min = min_revenu, name = brut_name)],
        period = period,
        parent1 = dict(
            birth = datetime.date(year - 40, 1, 1),
            ),
        )
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        **single_entity_kwargs).new_simulation(debug = True)
    brut = simulation.get_holder(brut_name).array
    imposable = simulation.calculate(imposable_name)

    inversion_reform = inversion_revenus.build_reform(tax_benefit_system)
    inverse_simulation = inversion_reform.new_scenario().init_single_entity(
        **single_entity_kwargs).new_simulation(debug = True)

    inverse_simulation.get_holder(brut_name).delete_arrays()
    inverse_simulation.get_or_new_holder(inversible_name).array = imposable.copy()
    new_brut = inverse_simulation.calculate(brut_name)
    pyplot.subplot(2, 1, 1)
    pyplot.plot(brut, imposable, 'ro', label = "direct")
    pyplot.plot(new_brut, imposable, 'db', label = "inversed")
    pyplot.legend()

    pyplot.subplot(2, 1, 2)
    pyplot.plot(brut, new_brut - brut, 'r-')

    pyplot.show()
    assert_near(new_brut, brut, absolute_error_margin = 1)


def net_plot(revenu, count = 11, max_revenu = 5000, min_revenu = 0):
    year = 2014
    period = periods.period("{}-01".format(year))
    if revenu == 'chomage':
        brut_name = 'chobrut'
        net_name = 'chonet'
    elif revenu == 'retraite':
        brut_name = 'rstbrut'
        net_name = 'rstnet'
    elif revenu == 'salaire':
        brut_name = 'salaire_de_base'
        net_name = 'salaire_net'
    else:
        return

    single_entity_kwargs = dict(
        axes = [[
            dict(count = count, max = max_revenu, min = min_revenu, name = brut_name)
            ]],
        period = period,
        parent1 = dict(
            birth = datetime.date(year - 40, 1, 1),
            ),
        )
    simulation = tax_benefit_system.new_scenario().init_single_entity(
        **single_entity_kwargs).new_simulation(debug = True)

    smic_horaire = simulation.legislation_at(period.start).cotsoc.gen.smic_h_b
    smic_mensuel =  smic_horaire * 35 * 52 / 12
    brut = simulation.get_holder(brut_name).array
    simulation.get_or_new_holder('contrat_de_travail').array =  brut < smic_mensuel # temps plein ou temps partiel
    simulation.get_or_new_holder('heures_remunerees_volume').array =  brut // smic_horaire # temps plein ou temps partiel

    net = simulation.calculate(net_name)

    inversion_reform = inversion_revenus.build_reform(tax_benefit_system)
    inverse_simulation = inversion_reform.new_scenario().init_single_entity(
        **single_entity_kwargs).new_simulation(debug = True)

    inverse_simulation.get_holder(brut_name).delete_arrays()
    inverse_simulation.get_or_new_holder(net_name).array = net.copy()
    inverse_simulation.get_or_new_holder('contrat_de_travail').array =  brut < smic_mensuel # temps plein ou temps partiel
    inverse_simulation.get_or_new_holder('heures_remunerees_volume').array =  (
        (brut // smic_horaire)  * (brut < smic_mensuel)
        )

    print inverse_simulation.get_or_new_holder('contrat_de_travail').array
    print inverse_simulation.get_or_new_holder('heures_remunerees_volume').array

    new_brut = inverse_simulation.calculate(brut_name)
    pyplot.subplot(2, 1, 1)
    pyplot.plot(brut, net, 'ro', label = "direct")
    pyplot.plot(new_brut, net, 'db', label = "inversed")
    pyplot.legend()

    pyplot.subplot(2, 1, 2)
    pyplot.plot(brut, new_brut - brut, 'r-')

    pyplot.show()
    assert_near(new_brut, brut, absolute_error_margin = 1)


if __name__ == '__main__':
    # chomage OK
    # brut_plot('chomage', count = 5000)
    # retraite OK (mais long !)
    # brut_plot('retraite', count = 10000)
    # brut_plot('salaire', count = 101, max_revenu = 2000, min_revenu = 0)

    # retraite OK
    # net_plot('retraite', count = 100)
    net_plot('chomage', count = 101, max_revenu = 4000, min_revenu = 0)
