
from odoo import api, fields, models, _, tools


class project_task_user_rel(models.Model):
    _name = 'project.task.user.rel'
    _description = 'Project Task User Rel'

    task_id = fields.Many2one('project.task', string='Task id')
    user_id = fields.Many2one('res.users', string='User id')
    whatsapp_msg_id = fields.Char(string='Whatsapp Message id')

