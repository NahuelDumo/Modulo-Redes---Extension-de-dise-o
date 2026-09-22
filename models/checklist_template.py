# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class ChecklistTemplate(models.Model):
    _inherit = 'design.checklist_template'

    is_simplified = fields.Boolean(
        string='Es Plantilla para Diseño Simplificado',
        default=False,
        help="Si está marcado, esta plantilla se utilizará por defecto para cargar el checklist corto en los Diseños Simplificados de Redes."
    )

    def _check_redes_admin_rights(self):
        user = self.env.user
        is_admin = (
            user.has_group('Modulo-Redes---Extension-de-dise-o.group_redes_admin') or
            user.has_group('project.group_project_manager') or
            self.env.is_superuser() or
            any(g.name in ['Administrador (Redes)', 'Administrador'] for g in user.groups_id)
        )
        if not is_admin:
            raise AccessError(_("Solo los Administradores de Redes Sociales pueden crear, modificar o eliminar plantillas de Checklist Corto (Simplificado)."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_simplified'):
                self._check_redes_admin_rights()
        return super(ChecklistTemplate, self).create(vals_list)

    def write(self, vals):
        if 'is_simplified' in vals or any(rec.is_simplified for rec in self):
            self._check_redes_admin_rights()
        return super(ChecklistTemplate, self).write(vals)

    def unlink(self):
        if any(rec.is_simplified for rec in self):
            self._check_redes_admin_rights()
        return super(ChecklistTemplate, self).unlink()


class ChecklistTemplateItem(models.Model):
    _inherit = 'design.checklist_template_item'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            template_id = vals.get('template_id')
            if template_id:
                template = self.env['design.checklist_template'].browse(template_id)
                if template.is_simplified:
                    template._check_redes_admin_rights()
        return super(ChecklistTemplateItem, self).create(vals_list)

    def write(self, vals):
        for rec in self:
            if rec.template_id.is_simplified:
                rec.template_id._check_redes_admin_rights()
        return super(ChecklistTemplateItem, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.template_id.is_simplified:
                rec.template_id._check_redes_admin_rights()
        return super(ChecklistTemplateItem, self).unlink()

