# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _register_hook(self):
        res = super()._register_hook()
        try:
            correct_root = self.env.ref('ModuloDisenoOdoo.menu_diseno_root', raise_if_not_found=False)
            if correct_root:
                duplicate_roots = self.env['ir.ui.menu'].search([
                    ('parent_id', '=', False),
                    ('id', '!=', correct_root.id),
                    ('name', 'in', ['Diseños', 'Redes', 'Módulo de Redes Sociales - Extensión de Diseños'])
                ])
                if duplicate_roots:
                    duplicate_roots.unlink()
                    _logger.info("Menú raíz duplicado eliminado exitosamente de ir.ui.menu")

                operaciones_menus = self.env['ir.ui.menu'].search([
                    ('parent_id', '=', correct_root.id),
                    ('name', '=', 'Operaciones')
                ])
                if operaciones_menus:
                    operaciones_menus.write({'name': 'Diseños', 'sequence': 10})
        except Exception as e:
            _logger.warning(f"No se pudo limpiar/renombrar menú en _register_hook: {e}")
        return res

    is_redes_project = fields.Boolean(
        string='Es Proyecto de Redes',
        default=False,
        help="Indica si este proyecto es de Gestión de Redes Sociales"
    )
    redes_plan_id = fields.Many2one(
        'redes.plan.template',
        string='Plan de Redes Contratado'
    )
    duracion_meses = fields.Integer(
        string='Duración en Meses',
        default=6,
        help="Cantidad de meses pactados en el contrato"
    )
    publis_por_mes = fields.Integer(
        string='Publicaciones por Mes',
        default=8,
        help="Cantidad de publicaciones mensuales planificadas"
    )
    dias_anticipacion_diseno = fields.Integer(
        string='Días de Anticipación para Diseño',
        default=5,
        help="Días antes de la fecha de publicación en que debe entregarse el diseño"
    )
    redes_sociales = fields.Char(
        string='Redes Sociales Contratadas',
        default='Instagram, Facebook'
    )
    fecha_inicio_redes = fields.Date(
        string='Fecha de Inicio de Contrato',
        default=fields.Date.today
    )
    
    # Responsables
    user_abril_id = fields.Many2one('res.users', string='Asignador / Líder (Abril)')
    user_vero_id = fields.Many2one('res.users', string='Coordinadora Reunión Interna (Vero)')
    user_barbara_id = fields.Many2one('res.users', string='Coordinadora Reunión Cliente (Bárbara)')

    tareas_redes_generadas = fields.Boolean(
        string='Tareas de Redes Generadas',
        default=False,
        copy=False
    )
    ultimo_mes_generado = fields.Integer(
        string='Último Mes Generado',
        default=0,
        copy=False
    )

    @api.onchange('redes_plan_id')
    def _onchange_redes_plan_id(self):
        """Autocompletar datos desde la plantilla de plan seleccionada"""
        if self.redes_plan_id:
            self.duracion_meses = self.redes_plan_id.duracion_meses
            self.publis_por_mes = self.redes_plan_id.publis_por_mes
            self.dias_anticipacion_diseno = self.redes_plan_id.dias_anticipacion_diseno
            self.redes_sociales = self.redes_plan_id.redes_sociales
            if self.redes_plan_id.user_abril_id:
                self.user_abril_id = self.redes_plan_id.user_abril_id
            if self.redes_plan_id.user_vero_id:
                self.user_vero_id = self.redes_plan_id.user_vero_id
            if self.redes_plan_id.user_barbara_id:
                self.user_barbara_id = self.redes_plan_id.user_barbara_id

    def _obtener_o_crear_etapa_inicial(self):
        """Asegura que existan etapas Kanban limpias en el proyecto y asigna las tareas a '1. Por Hacer'"""
        TaskStage = self.env['project.task.type']
        
        stages_data = [
            ('1. Por Hacer', 1),
            ('2. Redacción y Copys', 2),
            ('3. En Diseño Simplificado', 3),
            ('4. En Revisión (Abril)', 4),
            ('5. Programado / Publicado', 5),
            ('6. Finalizado', 6),
        ]
        
        created_stages = []
        for name, seq in stages_data:
            stage = TaskStage.search([('name', '=', name)], limit=1)
            if not stage:
                stage = TaskStage.create({'name': name, 'sequence': seq})
            if self.id not in stage.project_ids.ids:
                stage.write({'project_ids': [(4, self.id)]})
            created_stages.append(stage)

        return created_stages[0] if created_stages else False

    def _create_redes_task(self, vals, stage_id=None):
        """Helper para asignar usuarios y etapas en tareas soportando user_ids/user_id"""
        Task = self.env['project.task'].with_context(mail_create_nolog=True, mail_create_nosubscribe=True, tracking_disable=True)
        if stage_id:
            vals['stage_id'] = stage_id.id if hasattr(stage_id, 'id') else stage_id
        user_id = vals.pop('user_id', None)
        if user_id:
            if 'user_ids' in Task._fields:
                vals['user_ids'] = [(6, 0, [user_id])]
            elif 'user_id' in Task._fields:
                vals['user_id'] = user_id
        return Task.create(vals)

    def action_generar_tareas_redes(self):
        """Genera el Mes 1 por defecto al presionar o iniciar el proyecto"""
        return self.generar_mes_redes(mes_idx=1)

    def action_generar_proximo_mes(self):
        """Genera las tareas del siguiente mes del contrato"""
        self.ensure_one()
        siguiente_mes = (self.ultimo_mes_generado or 0) + 1
        if siguiente_mes > self.duracion_meses:
            raise UserError(_(f"Ya se han generado todos los {self.duracion_meses} meses de este contrato."))
        return self.generar_mes_redes(mes_idx=siguiente_mes)

    def generar_mes_redes(self, mes_idx=1):
        """
        Genera limpiamente las tareas del mes especificado (Mes 1, Mes 2, etc.),
        asignándoles las etapas Kanban correspondientes para mantener el tablero ordenado.
        """
        self.ensure_one()
        if not self.duracion_meses or self.duracion_meses <= 0:
            raise UserError(_("Por favor, especifica una duración en meses mayor a 0."))

        Design = self.env['design.design'].with_context(mail_create_nolog=True, mail_create_nosubscribe=True, tracking_disable=True)
        start_date = self.fecha_inicio_redes or fields.Date.today()
        stage_por_hacer = self._obtener_o_crear_etapa_inicial()

        _logger.info(f"Generando tareas de Redes para el Mes {mes_idx} del proyecto {self.name}.")

        # Si es el Mes 1, se genera la Estrategia inicial
        if mes_idx == 1:
            self._create_redes_task({
                'name': '1) Definición de Estrategia de Contenido',
                'project_id': self.id,
                'user_id': self.user_abril_id.id if self.user_abril_id else self.user_id.id,
                'date_deadline': start_date + timedelta(days=7),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'estrategia',
                'description': 'Establecer la estrategia inicial de contenido para las redes sociales del cliente.'
            }, stage_id=stage_por_hacer)

        mes_offset_days = (mes_idx - 1) * 30
        fecha_inicio_mes = start_date + timedelta(days=mes_offset_days)
        fecha_fin_mes = start_date + timedelta(days=mes_offset_days + 28)

        # 2. Armado de calendario (Mensual)
        self._create_redes_task({
            'name': f'2) Armado de calendario - Mes {mes_idx}',
            'project_id': self.id,
            'user_id': self.user_abril_id.id if self.user_abril_id else self.user_id.id,
            'date_deadline': fecha_inicio_mes + timedelta(days=3),
            'es_tarea_redes': True,
            'tipo_tarea_redes': 'calendario',
            'description': f'Planificación y armado del calendario de publicaciones del Mes {mes_idx}.'
        }, stage_id=stage_por_hacer)

        # 9. Armado de presentación con métricas (Mensual)
        self._create_redes_task({
            'name': f'9) Armado de presentación con métricas - Mes {mes_idx}',
            'project_id': self.id,
            'user_id': self.user_id.id if hasattr(self, 'user_id') else None,
            'date_deadline': fecha_fin_mes - timedelta(days=2),
            'es_tarea_redes': True,
            'tipo_tarea_redes': 'metricas_presentacion',
            'description': f'Elaborar informe y presentación de métricas correspondientes al Mes {mes_idx}.'
        }, stage_id=stage_por_hacer)

        # 10. Reunión interna de análisis de métricas (Mensual)
        self._create_redes_task({
            'name': f'10) Reunión interna de análisis de métricas - Mes {mes_idx}',
            'project_id': self.id,
            'user_id': self.user_vero_id.id if self.user_vero_id else (self.user_id.id if hasattr(self, 'user_id') else None),
            'date_deadline': fecha_fin_mes - timedelta(days=1),
            'es_tarea_redes': True,
            'tipo_tarea_redes': 'reunion_interna',
            'description': f'Coordinada por Vero. Análisis interno de rendimiento de publicaciones del Mes {mes_idx}.'
        }, stage_id=stage_por_hacer)

        # 11. Reunión con el cliente de análisis de métricas (Mensual/Periódica)
        self._create_redes_task({
            'name': f'11) Reunión con el cliente de análisis de métricas - Mes {mes_idx}',
            'project_id': self.id,
            'user_id': self.user_barbara_id.id if self.user_barbara_id else (self.user_id.id if hasattr(self, 'user_id') else None),
            'date_deadline': fecha_fin_mes,
            'es_tarea_redes': True,
            'tipo_tarea_redes': 'reunion_cliente',
            'description': f'Coordinada por Bárbara. Presentación de resultados y métricas del Mes {mes_idx} al cliente.'
        }, stage_id=stage_por_hacer)

        # Tareas Semanales dentro de este mes (4 semanas)
        for sem in range(1, 5):
            semana_global = ((mes_idx - 1) * 4) + sem
            fecha_semana = fecha_inicio_mes + timedelta(days=(sem - 1) * 7)

            # 3. Redacción de copys y contenidos
            self._create_redes_task({
                'name': f'3) Redacción de copys y contenidos - Semana {semana_global} (Mes {mes_idx})',
                'project_id': self.id,
                'date_deadline': fecha_semana + timedelta(days=2),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'copys',
                'description': f'Redacción de copys correspondientes a la Semana {semana_global}.'
            }, stage_id=stage_por_hacer)

            # 4. Revisión de contenidos
            self._create_redes_task({
                'name': f'4) Revisión de contenidos - Semana {semana_global} (Mes {mes_idx})',
                'project_id': self.id,
                'date_deadline': fecha_semana + timedelta(days=3),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'revision_copys',
                'description': f'Revisión y aprobación de los contenidos redactados para la Semana {semana_global}.'
            }, stage_id=stage_por_hacer)

            # 8. Verificación de publicación
            self._create_redes_task({
                'name': f'8) Verificación de publicación - Semana {semana_global} (Mes {mes_idx})',
                'project_id': self.id,
                'date_deadline': fecha_semana + timedelta(days=6),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'verificacion_semanal',
                'description': f'Auditoría de cumplimiento de publicaciones y archivo de diseños de la Semana {semana_global}.'
            }, stage_id=stage_por_hacer)

        # Tareas por Publicación e integración con Diseño Simplificado
        if self.publis_por_mes > 0:
            intervalo_dias = max(1, 28 // self.publis_por_mes)
            for p in range(1, self.publis_por_mes + 1):
                fecha_publi = fecha_inicio_mes + timedelta(days=(p - 1) * intervalo_dias + 5)
                fecha_diseno = fecha_publi - timedelta(days=self.dias_anticipacion_diseno)

                # Crear registro de Diseño Simplificado en el módulo de Diseños
                nuevo_diseno = Design.create({
                    'name': f'Diseño Simplificado - Publi {p} Mes {mes_idx} - {self.name}',
                    'cliente_id': self.partner_id.id if self.partner_id else self.env.user.partner_id.id,
                    'categoria_id': self.env['product.category'].search([], limit=1).id,
                    'es_diseno_simplificado': True,
                    'etapa': 'etapa1',
                    'visible_para_cliente': True
                })

                # 5. Diseño de cada publicación (Diseño Simplificado)
                task_diseno = self._create_redes_task({
                    'name': f'5) Diseño de publicación {p} (Mes {mes_idx}) - Diseño Simplificado',
                    'project_id': self.id,
                    'date_deadline': fecha_diseno,
                    'es_tarea_redes': True,
                    'tipo_tarea_redes': 'diseno_simplificado',
                    'design_id': nuevo_diseno.id,
                    'description': f'Diseño simplificado para la publicación {p} del Mes {mes_idx}. Incluye 1 sola etapa y checklist reducido.'
                }, stage_id=stage_por_hacer)
                nuevo_diseno.task_id = task_diseno.id

                # 6. Publicación de contenidos
                self._create_redes_task({
                    'name': f'6) Publicación de contenido {p} (Mes {mes_idx})',
                    'project_id': self.id,
                    'date_deadline': fecha_publi,
                    'es_tarea_redes': True,
                    'tipo_tarea_redes': 'publicacion',
                    'description': f'Programación o publicación efectiva de la pieza gráfica {p} del Mes {mes_idx}.'
                }, stage_id=stage_por_hacer)

        # 7. Configuración de campañas pagas (Únicamente en el Mes 1)
        if mes_idx == 1:
            redes_list = [r.strip() for r in (self.redes_sociales or 'Meta Ads').split(',') if r.strip()]
            for red in redes_list:
                self._create_redes_task({
                    'name': f'7) Configuración de campañas pagas - {red}',
                    'project_id': self.id,
                    'date_deadline': start_date + timedelta(days=10),
                    'es_tarea_redes': True,
                    'tipo_tarea_redes': 'campana_paga',
                    'red_social': red,
                    'description': f'Configuración y segmentación de campañas publicitarias pagas en {red}.'
                }, stage_id=stage_por_hacer)

        self.tareas_redes_generadas = True
        self.ultimo_mes_generado = mes_idx

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(f'Mes {mes_idx} de Redes Generado'),
                'message': _(f'Se generaron exitosamente las tareas del Mes {mes_idx} ({self.publis_por_mes} publicaciones y diseños simplificados).'),
                'type': 'success',
                'sticky': False,
            }
        }
