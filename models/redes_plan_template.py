# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class RedesPlanTemplate(models.Model):
    _name = 'redes.plan.template'
    _description = 'Plantilla de Plan de Redes Sociales'

    name = fields.Char(string='Nombre del Plan', required=True)
    duracion_meses = fields.Integer(string='Duración (Meses)', default=6, required=True,
                                    help="Cantidad de meses que durará el contrato")
    publis_por_mes = fields.Integer(string='Publicaciones por Mes', default=8, required=True,
                                    help="Cantidad de publicaciones acordadas por mes")
    publis_por_semana = fields.Integer(string='Publicaciones por Semana', default=2,
                                       help="Cantidad de publicaciones semanales pactadas")
    incluye_campana_paga = fields.Boolean(string='¿Incluye Campaña de Ads Paga?', default=False,
                                          help="Indica si incluye pauta publicitaria paga")
    cant_publis_pagas = fields.Integer(string='Cantidad de Publicaciones Pagas (Mes)', default=1,
                                       help="Cantidad de publicaciones o campañas con pauta publicitaria paga en el mes")
    dias_anticipacion_diseno = fields.Integer(string='Días de Anticipación para Diseño', default=5,
                                             help="Días antes de la fecha de publicación en que debe entregarse el diseño")
    redes_sociales = fields.Char(string='Redes Sociales', default='Instagram, Facebook',
                                 help="Redes sociales incluidas, separadas por coma")
    
    # Responsables asignados
    user_abril_id = fields.Many2one('res.users', string='Líder de Proceso / Asignador (Abril)',
                                    help="Usuario que asigna tareas y gestiona el proyecto")
    user_vero_id = fields.Many2one('res.users', string='Coordinadora Reunión Interna (Vero)',
                                   help="Coordinadora de la reunión interna de análisis de métricas")
    user_barbara_id = fields.Many2one('res.users', string='Coordinadora Reunión Cliente (Bárbara)',
                                     help="Coordinadora de la reunión con el cliente de análisis de métricas")
    
    active = fields.Boolean(string='Activo', default=True)

class RedesPlanLine(models.Model):
    _name = 'redes.plan.line'
    _description = 'Línea de Plan de Redes Sociales'

    plan_id = fields.Many2one('redes.plan.template', string='Plan de Redes', ondelete='cascade')
    name = fields.Char(string='Descripción / Título', required=True)
    red_social = fields.Char(string='Red Social (para Campañas)')
    frecuencia = fields.Selection([
        ('unica', 'Única (Inicio)'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('por_publicacion', 'Por Publicación')
    ], string='Frecuencia', default='mensual', required=True)
