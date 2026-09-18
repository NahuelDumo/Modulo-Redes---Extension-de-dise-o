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
    design_id = fields.Many2one('design.design', string='Diseño Simplificado Asociado', copy=False)

    es_diseno_simplificado = fields.Boolean(
        string='Es Diseño Simplificado',
        compute='_compute_es_diseno_simplificado',
        store=True
    )

    @api.depends('design_id', 'tipo_tarea_redes')
    def _compute_es_diseno_simplificado(self):
        for task in self:
            task.es_diseno_simplificado = bool(task.design_id and task.design_id.es_diseno_simplificado) or (task.tipo_tarea_redes == 'diseno_simplificado')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProjectTask, self).create(vals_list)
        for record in records:
            if record.design_id and record.design_id.task_id != record:
                record.design_id.task_id = record.id
        return records

    def copy(self, default=None):
        # Duplicar una publicación (Odoo copia también las subtareas): la subtarea de diseño recibe un diseño
        # nuevo en borrador en vez de compartir (y quitarle) el de la tarea original.
        default = dict(default or {})
        if self.design_id and 'design_id' not in default:
            d = self.design_id
            default['design_id'] = self.env['design.design'].sudo().create({
                'name': f"{d.name} (copia)",
                'cliente_id': d.cliente_id.id,
                'categoria_id': d.categoria_id.id,
                'es_diseno_simplificado': d.es_diseno_simplificado,
                'etapa': 'etapa1',
                'visible_para_cliente': d.visible_para_cliente,
            }).id
        return super().copy(default)

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'design_id' in vals:
            for record in self:
                if record.design_id and record.design_id.task_id != record:
                    record.design_id.task_id = record.id
        return res

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
