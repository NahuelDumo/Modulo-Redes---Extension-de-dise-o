# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class Design(models.Model):
    _inherit = 'design.design'

    es_diseno_simplificado = fields.Boolean(
        string='Es Diseño Simplificado',
        default=False,
        tracking=True,
        help="Los Diseños Simplificados poseen únicamente la Etapa 1 y un checklist de verificación reducido."
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Design, self).create(vals_list)
        for record in records:
            if record.es_diseno_simplificado:
                record._cargar_checklist_simplificado()
        return records

    def _cargar_checklist_simplificado(self):
        """Carga la plantilla de checklist corto/reducido para Diseños Simplificados"""
        self.ensure_one()
        # Buscar plantilla específica marcada como simplificada o buscar la plantilla estándar de la categoría
        template = self.env['design.checklist_template'].search([
            ('is_simplified', '=', True)
        ], limit=1)

        if template:
            # Eliminar ítems previos de la etapa
            self.checklist_ids.filtered(lambda x: x.etapa == 'etapa1').unlink()
            for item_template in template.item_ids:
                self.env['design.checklist_item'].create({
                    'name': item_template.name,
                    'design_id': self.id,
                    'etapa': 'etapa1',
                    'orden': item_template.orden,
                })
            _logger.info(f"Se cargó el checklist simplificado desde la plantilla '{template.name}' para el diseño {self.name}")

    def _transicion_a_etapa2_aprobado(self):
        """
        Sobrescritura para Diseños Simplificados:
        Si es Diseño Simplificado, OMITE la Etapa 2 y pasa directamente a Completado.
        """
        for record in self:
            if record.es_diseno_simplificado:
                record.write({
                    'etapa': 'completo',
                    'state': 'aprobado',
                    'aprobado_cliente': True,
                    'fecha_aprobacion_cliente': fields.Datetime.now()
                })
                record.message_post(
                    body=_("✅ **Diseño Simplificado Completado**: Aprobado exitosamente sin requerir Etapa 2."),
                    message_type="notification"
                )
                return True
        return super(Design, self)._transicion_a_etapa2_aprobado()
