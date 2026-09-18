# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Cuotas mensuales de Redes generadas el día 1 (la cuota 1 sale del presupuesto y no lo lleva)
    redes_project_id = fields.Many2one('project.project', string='Proyecto de Redes', index=True,
                                       readonly=True, domain=[('is_redes_project', '=', True)])
