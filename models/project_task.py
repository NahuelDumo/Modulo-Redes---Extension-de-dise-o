# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProjectTask(models.Model):
    _inherit = 'project.task'

    es_tarea_redes = fields.Boolean(
        string='Es Tarea de Redes',
        default=False,
        index=True
    )
    tipo_tarea_redes = fields.Selection([
        ('estrategia', '1. Estrategia de Contenido'),
        ('calendario', '2. Armado de Calendario'),
        ('copys', '3. Redacción de Copys'),
        ('revision_copys', '4. Revisión de Contenidos'),
        ('diseno_simplificado', '5. Diseño Simplificado'),
        ('publicacion', '6. Publicación de Contenidos'),
        ('campana_paga', '7. Configuración Campaña Paga'),
        ('verificacion_semanal', '8. Verificación de Publicación'),
        ('metricas_presentacion', '9. Presentación Métricas'),
        ('reunion_interna', '10. Reunión Interna Métricas'),
        ('reunion_cliente', '11. Reunión Cliente Métricas')
    ], string='Tipo de Tarea de Redes', index=True)

    red_social = fields.Char(string='Red Social (Campañas)')
    design_id = fields.Many2one('design.design', string='Diseño Simplificado Asociado')
    
    es_diseno_simplificado = fields.Boolean(
        string='Es Diseño Simplificado',
        compute='_compute_es_diseno_simplificado',
        store=True
    )

    @api.depends('design_id', 'tipo_tarea_redes')
    def _compute_es_diseno_simplificado(self):
        for task in self:
            task.es_diseno_simplificado = bool(task.design_id and task.design_id.es_diseno_simplificado) or (task.tipo_tarea_redes == 'diseno_simplificado')

    def action_open_associated_design(self):
        """Abre la vista formulario del diseño simplificado asociado"""
        self.ensure_one()
        if not self.design_id:
            raise models.UserError(_("Esta tarea no tiene un diseño simplificado asociado."))
        return {
            'name': _('Diseño Simplificado'),
            'type': 'ir.actions.act_window',
            'res_model': 'design.design',
            'res_id': self.design_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
