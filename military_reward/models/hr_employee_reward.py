from odoo import models, fields


class HrReward(models.Model):
    _name = 'hr.reward'
    _description = 'Reward'
    _order = 'level name'

    name = fields.Char(string="Name")
    image = fields.Image(string="Image")
    priority = fields.Integer(string="Priority")
    level = fields.Selection([
        ('state', 'state'),
        ('department', 'department'),
        ('unit', 'unit')
    ], groups="hr.group_hr_manager"
    )
    type = fields.Selection([
        ('honour', 'honour'),
        ('medal', 'medal'),
        ('award', 'award'),
        ('reward', 'reward')
    ],
    )
    product_id = fields.Many2one('product.product')
    reference = fields.Char(string="Reference")
    description = fields.Text(string="Description")


class HrRewardApplication(models.Model):
    _name = 'hr.reward.application'
    _description = 'Reward Application'
    _order = 'date desc'

    name = fields.Char('Application Reference',
                       required=True,
                       index=True,
                       copy=False,
                       default='New'
                       )
    category = fields.Selection(
        'Category',
        index=True,
        related='hr.employee.reward',
        store=True)
    author = fields.One2many(
        'hr.employee',
        'name',
        string="Author"
    )
    partner = fields.One2many(
        'res.partner',
        'name',
        string="Partner"
    )
    state = fields.Selection([])
    issue_date = fields.Date(string="Issue Date")
    issue_number = fields.Char(string="Issue Number")
    line_ids = fields.One2many(
        'hr.reward.application.line',
        'application_id',
        string="Reward History"
    )


class EmployeeRewardLine(models.Model):
    _name = "hr.reward.application.line"
    _description = "Employee Reward Lines"

    date = fields.Date(string="Date")
    number = fields.Char(string="Number")
    application_id = fields.Many2one(
        'hr.reward.application',
        string="Reward"
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee"
    )
    status = fields.Selection([
        ('draft', 'state'),
        ('confirmed', 'department'),
        ('canceled', 'unit'),
        ('issued', 'issued'),
        ('available', 'available'),
        ('handed', 'handed')])
    text = fields.Text(string="Application Text")
