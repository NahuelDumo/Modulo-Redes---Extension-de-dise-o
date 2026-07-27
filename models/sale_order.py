# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_redes_service = fields.Boolean(
        string='Tiene Servicio de Redes',
        compute='_compute_has_redes_service',
        store=True
    )
    redes_project_id = fields.Many2one(
        'project.project',
        string='Proyecto de Redes Creado',
        copy=False
    )

    @api.depends('order_line.product_id', 'order_line.product_id.categ_id', 'order_line.product_id.name')
    def _compute_has_redes_service(self):
        for order in self:
            has_redes = False
            for line in order.order_line:
                if line.product_id:
                    prod_name = (line.product_id.name or '').lower()
                    cat_name = (line.product_id.categ_id.name or '').lower() if line.product_id.categ_id else ''
                    if 'redes' in cat_name or 'rrss' in cat_name or 'redes' in prod_name or 'rrss' in prod_name:
                        has_redes = True
                        break
            order.has_redes_service = has_redes

    def action_confirm(self):
        """
        Al confirmar el presupuesto de venta (Sale Order):
        Si incluye un servicio de Redes Sociales (Categoría 'Redes' o productos 'RRSS'),
        crea/configura automáticamente el Proyecto de Redes y genera las 11 tareas.
        """
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.has_redes_service and not order.redes_project_id:
                order._crear_proyecto_redes_desde_presupuesto()
        return res

    def _crear_proyecto_redes_desde_presupuesto(self):
        """Crea el proyecto de Redes vinculado al Presupuesto y genera sus 11 tareas"""
        self.ensure_one()
        duracion_meses = 6
        product_name = ""

        # Determinar la duración según el nombre del producto (Anual, Semestral, Puntual) o cantidad
        for line in self.order_line:
            if line.product_id:
                pname = (line.product_id.name or '').lower()
                cname = (line.product_id.categ_id.name or '').lower() if line.product_id.categ_id else ''
                if 'redes' in cname or 'rrss' in cname or 'redes' in pname or 'rrss' in pname:
                    product_name = line.product_id.name
                    if 'anual' in pname:
                        duracion_meses = 12
                    elif 'semestral' in pname:
                        duracion_meses = 6
                    elif 'puntual' in pname:
                        duracion_meses = 1
                    elif line.product_uom_qty > 0:
                        duracion_meses = int(line.product_uom_qty)
                    break

        project_vals = {
            'name': f"{product_name or 'Redes Sociales'} - {self.partner_id.name} ({self.name})",
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            'is_redes_project': True,
            'duracion_meses': duracion_meses,
            'publis_por_mes': 8,
            'fecha_inicio_redes': fields.Date.today(),
            'description': f"Proyecto creado automáticamente desde el Presupuesto Aprobado {self.name}."
        }

        new_project = self.env['project.project'].create(project_vals)
        self.redes_project_id = new_project.id

        # Generar automáticamente las 11 tareas del contrato
        new_project.action_generar_tareas_redes()
        _logger.info(f"Proyecto de Redes {new_project.name} (Duración: {duracion_meses} meses) creado desde Presupuesto {self.name}.")

    def action_view_redes_project(self):
        """Acción de botón inteligente para ver el proyecto de redes vinculado"""
        self.ensure_one()
        if not self.redes_project_id:
            raise models.UserError(_("No hay un proyecto de Redes asignado a este presupuesto aún."))
        return {
            'name': _('Proyecto de Redes'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.redes_project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
