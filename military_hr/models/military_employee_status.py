from odoo import fields, models


class MilitaryEmployeeStatus(models.Model):
    _name = 'military.employee.status'
    _description = 'Employee Status'
    _order = 'sequence'
    _parent_name = 'parent_id'

    name = fields.Char(
        description='Status Name',
        required=True,
        default='Draft',
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    description = fields.Text(
        string='Description',
        help='Status description'
    )
    parent_id = fields.Many2one(
        'military.employee.status',
        index=True,
        ondelete='cascade',
        string='Parent Status'
    )
    child_ids = fields.One2many(
        'military.employee.status',
        'parent_id',
        string='Substatuses',
        readonly=True,
    )
