from odoo import models, fields, api

ls_grade = [('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8')]

ls_step = [('1', '1'),
           ('2', '2'),
           ('3', '3'),
           ('4', '4'),
           ('5', '5'),
           ('6', '6'),
           ('7', '7')]


class HrPayScaleAdministrative(models.Model):
    _name = 'hr.pay.scale.administrative'
    _description = 'Escala Salarial Administrativo'

    description = fields.Char(string='Descripción')
    grade = fields.Selection(ls_grade, string='Grado')
    step = fields.Selection(ls_step, string='Paso')
    wage = fields.Float(string='Salario ONAPRE', digits=(12, 2))
    wage_compensate = fields.Float(string='Salario Compensatorio', digits=(12, 2))
    company_id = fields.Many2one('res.company', string='Compañía')

    @api.depends('description', 'grade', 'step')
    def name_get(self):
        result = []
        for registro in self:
            name = str(registro.description) + ' ' + str(registro.grade) + ' ' + str(registro.step)
            result.append((registro.id, name))
        return result
