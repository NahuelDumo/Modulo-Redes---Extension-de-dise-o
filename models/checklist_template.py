# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ChecklistTemplate(models.Model):
    _inherit = 'design.checklist_template'

    is_simplified = fields.Boolean(
        string='Es Plantilla para Diseño Simplificado',
        default=False,
        help="Si está marcado, esta plantilla se utilizará por defecto para cargar el checklist corto en los Diseños Simplificados de Redes."
    )
