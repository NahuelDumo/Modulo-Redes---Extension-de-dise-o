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
        crea/configura automáticamente el Proyecto de Redes con sus etapas y tareas iniciales,
        y redirige al usuario a la pantalla de parámetros del proyecto.
        """
        res = super(SaleOrder, self).action_confirm()
        action_redirect = False
        for order in self:
            if order.has_redes_service and not order.redes_project_id:
                action_redirect = order._crear_proyecto_redes_desde_presupuesto()
        if action_redirect:
            return action_redirect
        return res

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Al crear la factura desde el presupuesto de venta:
        Si incluye un servicio de Redes Sociales y aún no tiene proyecto, asegura su creación.
        """
        moves = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)
        for order in self:
            if order.has_redes_service and not order.redes_project_id:
                order._crear_proyecto_redes_desde_presupuesto()
        return moves

    def _crear_proyecto_redes_desde_presupuesto(self):
        """Crea el proyecto de Redes vinculado al Presupuesto, inicializa etapas/tareas únicas y abre la pantalla"""
        self.ensure_one()
        duracion_meses = 1
        product_name = ""
        max_duration = 0

        # Determinar la duración evaluando todas las líneas de Redes
        for line in self.order_line:
            if line.product_id:
                pname = (line.product_id.name or '').lower()
                cname = (line.product_id.categ_id.name or '').lower() if line.product_id.categ_id else ''
                if 'redes' in cname or 'rrss' in cname or 'redes' in pname or 'rrss' in pname:
                    if not product_name:
                        product_name = line.product_id.name

                    current_dur = 1
                    if 'anual' in pname:
                        current_dur = 12
                        product_name = line.product_id.name
                    elif 'semestral' in pname:
                        current_dur = 6
                        product_name = line.product_id.name
                    elif 'puntual' in pname or 'perfil' in pname or 'creaci' in pname:
                        current_dur = 1
                    elif line.product_uom_qty > 0:
                        current_dur = int(line.product_uom_qty)

                    if current_dur > max_duration:
                        max_duration = current_dur

        duracion_meses = max_duration if max_duration > 0 else 6

        start_date = fields.Date.today()
        etapa_mes = self.env['project.project']._obtener_etapa_mes_proyecto(start_date)

        project_vals = {
            'name': f"{product_name or 'Redes Sociales'} - {self.partner_id.name} ({self.name})",
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            'is_redes_project': True,
            'duracion_meses': duracion_meses,
            'publis_por_mes': 8,
            'publis_por_semana': 2,
            'fecha_inicio_redes': start_date,
            'stage_id': etapa_mes.id if etapa_mes else False,
            'description': f"Proyecto creado automáticamente desde el Presupuesto Aprobado {self.name}."
        }

        new_project = self.env['project.project'].create(project_vals)
        self.redes_project_id = new_project.id

        _logger.info(f"Proyecto de Redes {new_project.name} (Duración: {duracion_meses} meses) creado desde Presupuesto {self.name} en etapa {etapa_mes.name if etapa_mes else 'Inicial'}.")

        # Abrir directamente el formulario del proyecto en su configuración
        return {
            'name': _('Parámetros de Proyecto de Redes'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': new_project.id,
            'view_mode': 'form',
            'target': 'current',
        }

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
