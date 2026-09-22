# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

MESES_ESP = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

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
                    ('name', 'in', ['Plantillas de Checklist', 'Plantillas de checklist', 'Diseños', 'Redes', 'Módulo de Redes Sociales - Extensión de Diseños'])
                ])
                if duplicate_roots:
                    duplicate_roots.unlink()
                    _logger.info("Menú huérfano 'Plantillas de Checklist' eliminado exitosamente de ir.ui.menu")

                operaciones_menus = self.env['ir.ui.menu'].search([
                    ('parent_id', '=', correct_root.id),
                    ('name', '=', 'Operaciones')
                ])
                if operaciones_menus:
                    operaciones_menus.write({'active': False})
                    _logger.info("Menú viejo Operaciones desactivado exitosamente")

            # Sincronización forzada de permisos de menús de Redes en base de datos
            admin_group = self.env.ref('Modulo-Redes---Extension-de-dise-o.group_redes_admin', raise_if_not_found=False)
            if not admin_group:
                admin_group = self.env['res.groups'].search([('name', '=', 'Administrador (Redes)')], limit=1)

            designer_group = self.env.ref('Modulo-Redes---Extension-de-dise-o.group_redes_designer', raise_if_not_found=False)
            if not designer_group:
                designer_group = self.env['res.groups'].search([('name', '=', 'Diseñador (Redes)')], limit=1)

            if admin_group:
                # 1. Menús exclusivos de Administrador: Proyectos, Calendario, Configuración, Planes, Checklist Corto
                admin_menu_names = [
                    'Proyectos de Redes',
                    'Calendario de Publicaciones',
                    'Configuración Redes',
                    'Planes de Redes',
                    'Checklist Corto (Simplificado)',
                    'Checklist Corto'
                ]
                admin_menus = self.env['ir.ui.menu'].search([('name', 'in', admin_menu_names)])
                for m in admin_menus:
                    m.write({'groups_id': [(6, 0, [admin_group.id])]})

                # 2. Menús compartidos: Tareas Pendientes Diseñadores, Diseños Simplificados
                if designer_group:
                    shared_menu_names = [
                        'Tareas Pendientes Diseñadores',
                        'Diseños Simplificados'
                    ]
                    shared_menus = self.env['ir.ui.menu'].search([('name', 'in', shared_menu_names)])
                    for m in shared_menus:
                        m.write({'groups_id': [(6, 0, [admin_group.id, designer_group.id])]})

                # 3. Acciones de ventana restringidas
                for act_name in ['Proyectos de Redes Sociales', 'Calendario de Publicaciones', 'Plantillas de Planes de Redes', 'Checklist Corto (Diseño Simplificado)']:
                    acts = self.env['ir.actions.act_window'].search([('name', '=', act_name)])
                    for act in acts:
                        act.write({'groups_id': [(6, 0, [admin_group.id])]})

                _logger.info("Permisos de menús de Redes Sociales sincronizados exitosamente en _register_hook")
        except Exception as e:
            _logger.warning(f"No se pudo sincronizar permisos de menús en _register_hook: {e}")
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
    publis_por_semana = fields.Integer(
        string='Publicaciones por Semana',
        default=2,
        help="Cantidad de publicaciones semanales prometidas"
    )
    incluye_campana_paga = fields.Boolean(
        string='¿Incluye Campaña de Ads Paga?',
        default=False,
        help="Indica si se deben generar tareas de campañas de publicidad paga (Ads)"
    )
    cant_publis_pagas = fields.Integer(
        string='Cantidad de Publicaciones Pagas (Mes)',
        default=1,
        help="Cantidad de publicaciones o campañas con pauta publicitaria paga en el mes"
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

    tareas_unicas_generadas = fields.Boolean(
        string='Tareas Únicas Generadas',
        default=False,
        copy=False
    )
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
    ultima_semana_generada = fields.Integer(
        string='Última Semana Generada',
        default=0,
        copy=False
    )

    @api.model
    def _obtener_etapa_mes_proyecto(self, fecha=None):
        """
        Obtiene el registro de la etapa de proyecto (project.project.stage)
        correspondiente al mes de la fecha indicada (ej. 'Agosto').
        """
        if 'project.project.stage' not in self.env:
            return False
        if not fecha:
            fecha = fields.Date.today()
        mes_num = fecha.month if hasattr(fecha, 'month') else datetime.strptime(str(fecha), '%Y-%m-%d').month
        mes_nombre = MESES_ESP.get(mes_num, '')
        if not mes_nombre:
            return False

        Stage = self.env['project.project.stage']
        stage = Stage.search([('name', '=ilike', mes_nombre)], limit=1)
        if not stage:
            stage = Stage.search([('name', 'ilike', mes_nombre)], limit=1)
        return stage

    @api.model
    def _cron_actualizar_etapas_mensuales_redes(self):
        """
        Cron automatizado diario:
        1. Revisa los proyectos de redes activos y los mueve automáticamente a la etapa del mes actual.
        2. Al empezar cada semana (lunes) genera la semana en curso (y el mes, si es nuevo).
        3. El día 1 de cada mes genera la factura en borrador de la cuota.
        """
        _logger.info("Ejecutando cron para actualizar etapas y avance semanal de Proyectos de Redes...")
        today = fields.Date.today()
        etapa_mes_actual = self._obtener_etapa_mes_proyecto(today)

        proyectos_redes = self.search([
            ('is_redes_project', '=', True),
            ('active', '=', True)
        ])
        for project in proyectos_redes:
            # 1. Actualizar etapa del mes si cambió
            if etapa_mes_actual and project.stage_id != etapa_mes_actual:
                project.write({'stage_id': etapa_mes_actual.id})
                _logger.info(f"Proyecto {project.name} movido automáticamente a la etapa de mes '{etapa_mes_actual.name}'.")

            # 2. Al empezar cada semana (lunes) se genera la semana en curso; si es de un mes nuevo, también el mes.
            # Sólo proyectos ya arrancados con "Generar Mes 1" (así no se genera antes de configurarlos).
            # Las semanas que quedaron atrás no se generan (sin tareas retroactivas).
            if project.tareas_redes_generadas:
                semana_actual = ((today - project._fecha_semana(1)).days // 7) + 1
                if (project.ultima_semana_generada or 0) < semana_actual <= (project.duracion_meses or 6) * 4:
                    project._generar_semana(semana_actual)
                    _logger.info(f"Cron generó la Semana {semana_actual} para el proyecto {project.name}.")

            # 3. Día 1: factura en borrador de la cuota del mes
            if today.day == 1:
                project._crear_factura_cuota(today)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            p_name = (vals.get('name') or '').lower()
            es_de_redes = (
                vals.get('is_redes_project') or
                ('redes' in p_name or 'rrss' in p_name)
            )
            if es_de_redes:
                vals['is_redes_project'] = True
                if not vals.get('stage_id'):
                    fecha_ref = vals.get('fecha_inicio_redes') or fields.Date.today()
                    etapa_mes = self._obtener_etapa_mes_proyecto(fecha_ref)
                    if etapa_mes:
                        vals['stage_id'] = etapa_mes.id

        projects = super(ProjectProject, self).create(vals_list)

        for project in projects:
            p_name = (project.name or '').lower()
            es_de_redes = (
                project.is_redes_project or
                (project.sale_order_id and getattr(project.sale_order_id, 'has_redes_service', False)) or
                ('redes' in p_name or 'rrss' in p_name)
            )
            if es_de_redes:
                if not project.is_redes_project:
                    project.is_redes_project = True
                
                if hasattr(project, 'stage_id') and (not project.stage_id or (project.stage_id.name or '').lower() == 'plantilla'):
                    etapa_mes = self._obtener_etapa_mes_proyecto(project.fecha_inicio_redes or fields.Date.today())
                    if etapa_mes:
                        project.stage_id = etapa_mes.id

                if not project.tareas_unicas_generadas:
                    stages_dict = project._obtener_o_crear_etapas_redes()
                    project._generar_tareas_unicas(stages_dict, project.fecha_inicio_redes or fields.Date.today())

        return projects

    def _check_redes_access(self):
        """Administrador de Proyectos: todo. Administrador (Redes): sólo proyectos de Redes.
        Va en Python y no en ir.rule porque la regla de Usuario de Proyecto se sumaría (OR) y habilitaría todos."""
        self.check_access_rights('write')
        self.check_access_rule('write')
        if (not self.env.su
                and not self.env.user.has_group('project.group_project_manager')
                and not all(self.mapped('is_redes_project'))):
            raise AccessError(_("Sólo podés editar proyectos de Redes Sociales."))

    def write(self, vals):
        # is_favorite se ignora: Odoo lo guarda aparte y cualquier usuario puede marcar favoritos.
        if set(vals) - {'is_favorite'}:
            self._check_redes_access()
        return super().write(vals)

    @api.onchange('publis_por_semana')
    def _onchange_publis_por_semana(self):
        if self.publis_por_semana:
            self.publis_por_mes = self.publis_por_semana * 4

    @api.onchange('publis_por_mes')
    def _onchange_publis_por_mes(self):
        if self.publis_por_mes and not self.publis_por_semana:
            self.publis_por_semana = max(1, self.publis_por_mes // 4)

    @api.onchange('redes_plan_id')
    def _onchange_redes_plan_id(self):
        """Autocompletar datos desde la plantilla de plan seleccionada"""
        if self.redes_plan_id:
            self.duracion_meses = self.redes_plan_id.duracion_meses
            self.publis_por_mes = self.redes_plan_id.publis_por_mes
            self.publis_por_semana = getattr(self.redes_plan_id, 'publis_por_semana', 2) or max(1, self.publis_por_mes // 4)
            self.incluye_campana_paga = getattr(self.redes_plan_id, 'incluye_campana_paga', False)
            self.cant_publis_pagas = getattr(self.redes_plan_id, 'cant_publis_pagas', 1)
            self.dias_anticipacion_diseno = self.redes_plan_id.dias_anticipacion_diseno
            self.redes_sociales = self.redes_plan_id.redes_sociales
            if self.redes_plan_id.user_abril_id:
                self.user_abril_id = self.redes_plan_id.user_abril_id
            if self.redes_plan_id.user_vero_id:
                self.user_vero_id = self.redes_plan_id.user_vero_id
            if self.redes_plan_id.user_barbara_id:
                self.user_barbara_id = self.redes_plan_id.user_barbara_id

    def _obtener_o_crear_etapas_redes(self):
        """
        Asegura que existan ÚNICA Y EXCLUSIVAMENTE las 7 etapas Kanban oficiales de la plantilla:
        1. Administración - Recepción
        2. Configuración General
        3. Gestión Mensual
        4. Gestión Semanal de Publicaciones
        5. Administración - mensual
        6. Administración - cierre
        7. Gestión de Deuda
        Limpia cualquier columna duplicada o huérfana en el proyecto.
        """
        TaskStage = self.env['project.task.type']
        
        stages_data = [
            ('Administración - Recepción', 10),
            ('Configuración General', 20),
            ('Gestión Mensual', 30),
            ('Gestión Semanal de Publicaciones', 40),
            ('Administración - mensual', 50),
            ('Administración - cierre', 60),
            ('Gestión de Deuda', 70),
        ]
        
        stages_dict = {}
        official_stage_ids = []
        for name, seq in stages_data:
            stage = TaskStage.search([('name', '=', name)], order='id asc', limit=1)
            if not stage:
                stage = TaskStage.create({'name': name, 'sequence': seq})
            elif stage.sequence != seq:
                stage.write({'sequence': seq})
                
            stages_dict[name] = stage
            official_stage_ids.append(stage.id)

        # Establecer las etapas exactas en el proyecto eliminando duplicados
        self.write({'type_ids': [(6, 0, official_stage_ids)]})

        return stages_dict

    def _create_redes_task(self, vals, stage_id=None):
        """Helper para crear o actualizar tareas de redes evitando duplicados por nombre y jerarquía"""
        Task = self.env['project.task'].with_context(mail_create_nolog=True, mail_create_nosubscribe=True, tracking_disable=True)
        if stage_id:
            vals['stage_id'] = stage_id.id if hasattr(stage_id, 'id') else stage_id
        user_id = vals.pop('user_id', None)
        if user_id:
            if 'user_ids' in Task._fields:
                vals['user_ids'] = [(6, 0, [user_id])]
            elif 'user_id' in Task._fields:
                vals['user_id'] = user_id

        # Evitar duplicados: Si ya existe una tarea con este nombre y mismo parent en el proyecto, actualizarla
        t_name = vals.get('name')
        t_parent = vals.get('parent_id')
        if t_name and self.id:
            tarea_existente = self.task_ids.filtered(
                lambda t: t.name == t_name and (t.parent_id.id if t.parent_id else False) == (t_parent if t_parent else False)
            )
            if tarea_existente:
                tarea_existente.write(vals)
                return tarea_existente[0]

        return Task.create(vals)

    def _get_nombre_mes(self, fecha):
        """Retorna el nombre del mes y año en español (ej. 'Agosto 2026')"""
        if not fecha:
            fecha = fields.Date.today()
        mes_num = fecha.month if hasattr(fecha, 'month') else datetime.strptime(str(fecha), '%Y-%m-%d').month
        year = fecha.year if hasattr(fecha, 'year') else datetime.strptime(str(fecha), '%Y-%m-%d').year
        return f"{MESES_ESP.get(mes_num, '')} {year}".strip()

    def _generar_tareas_unicas(self, stages_dict, start_date):
        """
        Genera una sola vez las tareas generales de la plantilla en sus etapas correspondientes:
        - Administración - Recepción (4 tareas)
        - Configuración General (3 tareas)
        - Administración - cierre (3 tareas)
        - Gestión de Deuda (3 tareas)
        """
        self.ensure_one()
        _logger.info(f"Generando tareas de única vez para el proyecto de Redes {self.name}.")

        # 1. Administración - Recepción
        st_recepcion = stages_dict.get('Administración - Recepción')
        tareas_recepcion = [
            'Cargar en planilla "Cuenta Cliente"',
            'Cobro de Seña',
            'Incluir en planificación de trabajo: planilla on-line y pizarra',
            'Cargar en planilla ingresos/egresos Dirección'
        ]
        for idx, t_name in enumerate(tareas_recepcion, 1):
            self._create_redes_task({
                'name': t_name,
                'project_id': self.id,
                'user_id': self.user_id.id if hasattr(self, 'user_id') and self.user_id else None,
                'date_deadline': start_date + timedelta(days=idx),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'estrategia',
                'description': f'Tarea inicial de recepción y onboarding del cliente: {t_name}.'
            }, stage_id=st_recepcion)

        # 2. Configuración General
        st_config = stages_dict.get('Configuración General')
        tareas_config = [
            ('Revisión y aprobación del Plan - Estrategia de contenido', 7, self.user_abril_id.id if self.user_abril_id else None),
            ('Creación / Ajuste e Perfiles (cuando corresponda)', 10, self.user_abril_id.id if self.user_abril_id else None),
            ('Diseño de Plantillas (cuando corresponda)', 14, None)
        ]
        for t_name, offset_days, uid in tareas_config:
            self._create_redes_task({
                'name': t_name,
                'project_id': self.id,
                'user_id': uid,
                'date_deadline': start_date + timedelta(days=offset_days),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'estrategia',
                'description': f'Configuración general y estrategia: {t_name}.'
            }, stage_id=st_config)

        # 6. Administración - cierre (Al final del contrato)
        st_cierre = stages_dict.get('Administración - cierre')
        fecha_fin_contrato = start_date + timedelta(days=(self.duracion_meses or 6) * 30)
        tareas_cierre = [
            'Sacar de planificación de trabajo/borrar pizarra',
            'Archivo de carpeta física del cliente',
            'Medición de satisfacción al cliente / google'
        ]
        for idx, t_name in enumerate(tareas_cierre, 1):
            self._create_redes_task({
                'name': t_name,
                'project_id': self.id,
                'user_id': self.user_id.id if hasattr(self, 'user_id') and self.user_id else None,
                'date_deadline': fecha_fin_contrato + timedelta(days=idx),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'reunion_cliente',
                'description': f'Tareas de cierre de proyecto al finalizar el contrato: {t_name}.'
            }, stage_id=st_cierre)

        # 7. Gestión de Deuda
        st_deuda = stages_dict.get('Gestión de Deuda')
        tareas_deuda = [
            '1er Reclamo x mail cobranza y ws/tel al cliente',
            '2do Reclamo x mail cobranza y ws/tel al cliente',
            '3er Reclamo x mail cobranza y ws/tel al cliente'
        ]
        for idx, t_name in enumerate(tareas_deuda, 1):
            self._create_redes_task({
                'name': t_name,
                'project_id': self.id,
                'user_id': self.user_id.id if hasattr(self, 'user_id') and self.user_id else None,
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'reunion_interna',
                'description': f'Protocolo de gestión de cobranza y mora: {t_name}.'
            }, stage_id=st_deuda)

        self.tareas_unicas_generadas = True

    def action_generar_tareas_redes(self):
        """Genera las etapas, las tareas únicas y el Mes 1 con sus publicaciones"""
        # Los botones crean/borran tareas, etapas y diseños: se valida acceso al proyecto y se ejecuta con sudo
        self._check_redes_access()
        return self.sudo().generar_mes_redes(mes_idx=1)

    def action_regenerar_mes_1(self):
        """
        Regenera limpiamente el Mes 1 eliminando tareas y diseños previos del proyecto
        para limpiar cualquier duplicado previo.
        """
        self.ensure_one()
        self._check_redes_access()
        self = self.sudo()
        _logger.info(f"Regenerando limpiamente Mes 1 para el proyecto {self.name}")

        # Tareas de redes anteriores en este proyecto
        tareas_redes = self.task_ids.filtered(lambda t: t.es_tarea_redes or t.tipo_tarea_redes or t.design_id)
        disenos_a_borrar = tareas_redes.mapped('design_id')

        # Eliminar tareas duplicadas/viejas
        tareas_redes.unlink()
        if disenos_a_borrar:
            disenos_a_borrar.filtered(lambda d: d.state in ['borrador', 'validacion', 'cliente', 'correcciones_solicitadas']).unlink()

        self.tareas_unicas_generadas = False
        self.tareas_redes_generadas = False
        self.ultimo_mes_generado = 0
        self.ultima_semana_generada = 0

        return self.generar_mes_redes(mes_idx=1)

    def action_generar_proximo_mes(self):
        """Genera las tareas del siguiente mes del contrato"""
        self.ensure_one()
        self._check_redes_access()
        self = self.sudo()
        siguiente_mes = (self.ultimo_mes_generado or 0) + 1
        if siguiente_mes > self.duracion_meses:
            raise UserError(_(f"Ya se han generado todos los {self.duracion_meses} meses de este contrato."))
        return self.generar_mes_redes(mes_idx=siguiente_mes)

    def action_generar_proxima_semana(self):
        """Genera las tareas de la siguiente semana de publicaciones"""
        self.ensure_one()
        self._check_redes_access()
        self = self.sudo()

        siguiente_semana = (self.ultima_semana_generada or 0) + 1
        if ((siguiente_semana - 1) // 4) + 1 > self.duracion_meses:
            raise UserError(_(f"Ya se han generado todas las semanas para los {self.duracion_meses} meses de contrato."))

        self._generar_semana(siguiente_semana)
        nombre_mes = self._get_nombre_mes(self._fecha_semana(siguiente_semana))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(f'Semana {siguiente_semana} Generada'),
                'message': _(f'Se generaron las publicaciones y verificación de la Semana {siguiente_semana} ({nombre_mes}).'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _fecha_semana(self, semana):
        """Lunes de la semana N del contrato: las semanas arrancan el lunes, no el día en que se generan."""
        inicio = self.fecha_inicio_redes or fields.Date.today()
        return inicio + timedelta(days=7 * (semana - 1) - inicio.weekday())

    def _generar_semana(self, semana):
        """Genera la semana N. Si pertenece a un mes todavía no generado, genera primero el mes
        (tareas mensuales + su 1ª semana), igual que el cron y el botón 'Generar Próxima Semana'."""
        mes = ((semana - 1) // 4) + 1
        if mes > (self.ultimo_mes_generado or 0):
            self.generar_mes_redes(mes_idx=mes)
        if semana > (self.ultima_semana_generada or 0):
            fecha_semana = self._fecha_semana(semana)
            self._generar_semana_publicaciones(self._obtener_o_crear_etapas_redes(), semana, mes,
                                               fecha_semana, self._get_nombre_mes(fecha_semana))
            self.ultima_semana_generada = semana

    def _generar_semana_publicaciones(self, stages_dict, semana_global, mes_idx, fecha_semana, nombre_mes):
        """
        Genera la estructura semanal en 'Gestión Semanal de Publicaciones':
        - 1 Grupo (Tarea Padre) por cada publicación y red social, con sus 4 subtareas adentro:
          1. Redacción de Copys
          2. Diseño Simplificado (con diseño asociado)
          3. Revisión y Aprobación
          4. Publicación y Programación
        - 1 Tarea a la semana de 'Verificación Semanal Publicaciones'
        - Publicación de campaña paga (con cantidad de publis pagas) solo si está seleccionado
        """
        Design = self.env['design.design'].with_context(mail_create_nolog=True, mail_create_nosubscribe=True, tracking_disable=True)
        st_semanal = stages_dict.get('Gestión Semanal de Publicaciones')
        cant_publis = self.publis_por_semana or max(1, (self.publis_por_mes or 8) // 4)
        red_nombre = self.redes_sociales or 'Meta'

        # 1. Armado de cada publicación: 1 GRUPO (Tarea Padre) por cada publicación y red social
        for p in range(1, cant_publis + 1):
            # Repartidas de lunes a viernes: 1 → mié, 2 → mar/jue, 3 → lun/mié/vie (los fines de semana se editan a mano)
            fecha_publi = fecha_semana + timedelta(days=(2 * p - 1) * 5 // (2 * cant_publis))
            fecha_diseno = fecha_publi - timedelta(days=self.dias_anticipacion_diseno or 5)

            # Tarea Padre (El grupo visible en el tablero Kanban)
            parent_task = self._create_redes_task({
                'name': f'Armado de cada publicación (Publi {p} - {red_nombre} - Sem {semana_global} {nombre_mes})',
                'project_id': self.id,
                'user_id': self.user_abril_id.id if self.user_abril_id else None,
                'date_deadline': fecha_publi,
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'estrategia',
                'description': f'Grupo de trabajo de la publicación {p} ({red_nombre}) para la Semana {semana_global} ({nombre_mes}).'
            }, stage_id=st_semanal)

            # Subtarea 1: Redacción de Copys
            self._create_redes_task({
                'name': f'1. Redacción de Copys (Publi {p} - {red_nombre} - Sem {semana_global} {nombre_mes})',
                'parent_id': parent_task.id,
                'project_id': self.id,
                'user_id': self.user_abril_id.id if self.user_abril_id else None,
                'date_deadline': fecha_diseno - timedelta(days=2),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'copys',
                'description': f'Redacción de textos, propuesta conceptual y copy para la publicación {p}.'
            }, stage_id=st_semanal)

            # Subtarea 2: Diseño Simplificado (Con diseño vinculado para el diseñador)
            nuevo_diseno = Design.create({
                'name': f'Diseño Simplificado - Publi {p} Sem {semana_global} ({nombre_mes}) - {self.name}',
                'cliente_id': self.partner_id.id if self.partner_id else self.env.user.partner_id.id,
                'categoria_id': self.env['product.category'].search([], limit=1).id,
                'es_diseno_simplificado': True,
                'etapa': 'etapa1',
                'visible_para_cliente': True
            })

            subtask_diseno = self._create_redes_task({
                'name': f'2. Diseño Simplificado (Publi {p} - {red_nombre} - Sem {semana_global} {nombre_mes})',
                'parent_id': parent_task.id,
                'project_id': self.id,
                'user_id': self.user_abril_id.id if self.user_abril_id else None,
                'date_deadline': fecha_diseno,
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'diseno_simplificado',
                'design_id': nuevo_diseno.id,
                'description': f'Elaboración del arte visual y gráfico para la publicación {p}.'
            }, stage_id=st_semanal)
            nuevo_diseno.task_id = subtask_diseno.id

            # Subtarea 3: Revisión y Aprobación
            self._create_redes_task({
                'name': f'3. Revisión y Aprobación (Publi {p} - {red_nombre} - Sem {semana_global} {nombre_mes})',
                'parent_id': parent_task.id,
                'project_id': self.id,
                'user_id': self.user_abril_id.id if self.user_abril_id else None,
                'date_deadline': fecha_publi - timedelta(days=1),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'revision_copys',
                'description': f'Revisión interna y validación final del arte y texto antes de la publicación.'
            }, stage_id=st_semanal)

            # Subtarea 4: Publicación y Programación
            self._create_redes_task({
                'name': f'4. Publicación y Programación (Publi {p} - {red_nombre} - Sem {semana_global} {nombre_mes})',
                'parent_id': parent_task.id,
                'project_id': self.id,
                'user_id': self.user_abril_id.id if self.user_abril_id else None,
                'date_deadline': fecha_publi,
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'publicacion',
                'description': f'Programación y publicación oficial en las redes sociales acordadas ({red_nombre}).'
            }, stage_id=st_semanal)

        # 2. UNA TAREA A LA SEMANA de Verificación Semanal Publicaciones
        self._create_redes_task({
            'name': f'Verificación Semanal Publicaciones - Sem {semana_global} ({nombre_mes})',
            'project_id': self.id,
            'user_id': self.user_abril_id.id if self.user_abril_id else None,
            'date_deadline': fecha_semana + timedelta(days=4),
            'es_tarea_redes': True,
            'tipo_tarea_redes': 'verificacion_semanal',
            'description': f'Auditoría y verificación semanal de publicaciones programadas para la Semana {semana_global}.'
        }, stage_id=st_semanal)

        # 3. Publicación de campaña paga (con nombre y cantidad de publis pagas, solo si está seleccionado)
        if self.incluye_campana_paga:
            cant_pagas_mes = self.cant_publis_pagas or 1
            semana_del_mes = ((semana_global - 1) % 4) + 1

            generar_esta_semana = False
            if cant_pagas_mes == 1 and semana_del_mes == 1:
                generar_esta_semana = True
            elif cant_pagas_mes == 2 and semana_del_mes in [1, 3]:
                generar_esta_semana = True
            elif cant_pagas_mes == 3 and semana_del_mes in [1, 2, 3]:
                generar_esta_semana = True
            elif cant_pagas_mes >= 4:
                generar_esta_semana = True

            if generar_esta_semana:
                self._create_redes_task({
                    'name': f'Publicación de campaña paga ({cant_pagas_mes} publis pagas contratadas - {red_nombre} - Sem {semana_global} {nombre_mes})',
                    'project_id': self.id,
                    'user_id': self.user_abril_id.id if self.user_abril_id else None,
                    'date_deadline': fecha_semana + timedelta(days=4),
                    'es_tarea_redes': True,
                    'tipo_tarea_redes': 'campana_paga',
                    'red_social': red_nombre,
                    'description': f'Configuración y activación de pauta / campaña paga ({cant_pagas_mes} publicaciones pagas en el mes) para la Semana {semana_global}.'
                }, stage_id=st_semanal)

    def _crear_factura_cuota(self, hoy):
        """Día 1 de cada mes: factura en BORRADOR de la próxima cuota, vinculada al proyecto.
        - La cuota 1 se factura desde el presupuesto al aprobarse: acá se generan de la 2 a la N.
        - Precio del presupuesto = precio por mes. Cada cuota copia la anterior, así el ajuste manual
          por IPC (cada 3 meses) se arrastra; el administrativo revisa, confirma y envía."""
        order = self.env['sale.order'].sudo().search([('redes_project_id', '=', self.id)], limit=1)
        if not order or self.create_date.date() >= hoy:
            return  # sin presupuesto, o el proyecto arrancó este mismo mes (la 1ª cuota ya salió del presupuesto)
        Move = self.env['account.move'].sudo()
        cuotas = Move.search([('redes_project_id', '=', self.id), ('state', '!=', 'cancel')], order='id desc')
        numero = len(cuotas) + 2
        if numero > (self.duracion_meses or 0) or (cuotas and cuotas[0].create_date.date() == hoy):
            return  # contrato terminado, o ya se generó hoy
        ref = f"Cuota {numero}/{self.duracion_meses} {self._get_nombre_mes(hoy)} - {self.name}"
        if cuotas:
            Move.browse(cuotas[0].id).copy({'ref': ref, 'invoice_date': False})
            return
        lineas = order.order_line.filtered(lambda l: l._es_linea_redes())
        if not lineas:
            return
        vals = order._prepare_invoice()  # cliente, diario, condiciones de pago y origen = presupuesto
        vals.update({'ref': ref, 'redes_project_id': self.id, 'invoice_line_ids': []})
        for l in lineas:
            # Sin sale_line_ids: un presupuesto de Redes tiene muchas facturas y vincularlas a la línea
            # lo daría por sobrefacturado / sugeriría notas de crédito al volver a facturar desde la venta.
            linea = l._prepare_invoice_line(quantity=1)
            linea.pop('sale_line_ids', None)
            vals['invoice_line_ids'].append((0, 0, linea))
        Move.create(vals)

    def generar_mes_redes(self, mes_idx=1):
        """
        Genera limpiamente las etapas oficiales, tareas de única vez (si es Mes 1)
        y las tareas de Gestión Mensual, Administración - mensual y la PRIMERA SEMANA activa del mes.
        Las siguientes semanas se van generando progresivamente a medida que transcurre el calendario.
        """
        self.ensure_one()
        if not self.duracion_meses or self.duracion_meses <= 0:
            raise UserError(_("Por favor, especifica una duración en meses mayor a 0."))

        stages_dict = self._obtener_o_crear_etapas_redes()
        start_date = self.fecha_inicio_redes or fields.Date.today()

        _logger.info(f"Generando tareas de Redes para el Mes {mes_idx} del proyecto {self.name}.")

        # Si es el Mes 1 y no se crearon las tareas únicas, generarlas
        if mes_idx == 1 and not self.tareas_unicas_generadas:
            self._generar_tareas_unicas(stages_dict, start_date)

        mes_offset_days = (mes_idx - 1) * 30
        fecha_inicio_mes = start_date + timedelta(days=mes_offset_days)
        nombre_mes = self._get_nombre_mes(fecha_inicio_mes)

        # 3. Tareas en 'Gestión Mensual' (5 tareas)
        st_gestion_mensual = stages_dict.get('Gestión Mensual')
        tareas_gestion_mensual = [
            (f'Completar Calendario Mensual de Publicaciones ({nombre_mes})', 3, self.user_abril_id.id if self.user_abril_id else None, 'calendario'),
            (f'Revisión y aprobación Calendario ({nombre_mes})', 5, self.user_abril_id.id if self.user_abril_id else None, 'revision_copys'),
            (f'Armado métricas mensuales ({nombre_mes})', 26, self.user_id.id if hasattr(self, 'user_id') and self.user_id else None, 'metricas_presentacion'),
            (f'Reunión Interna Métricas mensuales ({nombre_mes})', 27, self.user_vero_id.id if self.user_vero_id else None, 'reunion_interna'),
            (f'Reunión con Cliente x Métricas ({nombre_mes})', 28, self.user_barbara_id.id if self.user_barbara_id else None, 'reunion_cliente')
        ]
        for t_name, day_offset, uid, tipo in tareas_gestion_mensual:
            self._create_redes_task({
                'name': t_name,
                'project_id': self.id,
                'user_id': uid,
                'date_deadline': fecha_inicio_mes + timedelta(days=day_offset),
                'es_tarea_redes': True,
                'tipo_tarea_redes': tipo,
                'description': f'Gestión mensual correspondiente a {nombre_mes}.'
            }, stage_id=st_gestion_mensual)

        # 5. Tareas en 'Administración - mensual' (2 tareas)
        st_admin_mensual = stages_dict.get('Administración - mensual')
        tareas_admin_mensual = [
            (f'Cobranza de cuota mensual al cliente ({nombre_mes})', 5),
            (f'Registro de cobranza mensual ({nombre_mes})', 10)
        ]
        for t_name, day_offset in tareas_admin_mensual:
            self._create_redes_task({
                'name': t_name,
                'project_id': self.id,
                'user_id': self.user_id.id if hasattr(self, 'user_id') and self.user_id else None,
                'date_deadline': fecha_inicio_mes + timedelta(days=day_offset),
                'es_tarea_redes': True,
                'tipo_tarea_redes': 'estrategia',
                'description': f'Administración mensual correspondiente a {nombre_mes}.'
            }, stage_id=st_admin_mensual)

        # 4. Generar ÚNICAMENTE la Semana 1 activa del mes en 'Gestión Semanal de Publicaciones' (arranca el lunes)
        semana_1_global = ((mes_idx - 1) * 4) + 1
        fecha_semana_1 = self._fecha_semana(semana_1_global)
        self._generar_semana_publicaciones(stages_dict, semana_1_global, mes_idx, fecha_semana_1, self._get_nombre_mes(fecha_semana_1))

        self.tareas_redes_generadas = True
        self.ultimo_mes_generado = mes_idx
        self.ultima_semana_generada = semana_1_global

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(f'Mes {mes_idx} ({nombre_mes}) - Semana {semana_1_global} Generada'),
                'message': _(f'Se generaron las tareas del Mes {mes_idx} y las publicaciones de la Semana {semana_1_global}. Las siguientes semanas se cargarán progresivamente.'),
                'type': 'success',
                'sticky': False,
            }
        }

