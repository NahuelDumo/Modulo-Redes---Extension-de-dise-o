# -*- coding: utf-8 -*-
{
    'name': 'Módulo de Redes Sociales - Extensión de Diseños',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Gestión de proyectos de Redes Sociales, automatización por meses, 11 etapas de trabajo y Diseño Simplificado',
    'description': """
        Extensión del Módulo de Diseños y Proyectos para la gestión integral de servicios de Redes Sociales:
        - Conexión automática desde Presupuestos (sale.order) al aprobar la venta.
        - Barra de navegación superior: Menú Redes junto a Diseños.
        - Generación automática de tareas según meses de contrato (Ej. 6 meses).
        - 11 Etapas / Tareas del proceso de Redes (Estrategia, Calendario, Copys, Revisión, Diseño Simplificado, Publicación, Campañas, Verificación, Métricas y Reuniones).
        - Proceso de Diseño Simplificado (1 sola etapa, checklist corto editable por Administrador de Redes, aprobación y rechazo).
        - Tablero dedicado de Tareas Pendientes de Diseñadores para Abril.
        - Asignación de permisos Administrador (Redes) y Diseñador (Redes) en Ajustes > Usuarios.
    """,
    'author': 'Nahuel Dumo / VEO',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'project',
        'sale_management',
        'mail',
        'ModuloListasDeVerificación'
    ],
    'data': [
        # Seguridad
        'security/security.xml',
        'security/ir.model.access.csv',

        # Vistas principales
        'views/menu.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/design_views.xml',
        'views/checklist_template_views.xml',
        'views/redes_plan_views.xml',
        'views/sale_order_views.xml',

        # Datos por defecto
        'data/default_redes_data.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
