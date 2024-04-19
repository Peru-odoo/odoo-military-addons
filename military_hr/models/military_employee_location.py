from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class MilitaryEmployeeLocation(models.Model):
    _name = "military.employee.location"
    _description = "Employee Location"
    _parent_store = True
    _parent_name = "parent_id"
    _order = 'complete_name, id'
    _rec_name = 'complete_name'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Work Location", required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    location_number = fields.Char()
    parent_id = fields.Many2one(
        'military.employee.location',
        'Parent Location',
        index=True,
    )
    child_ids = fields.One2many(
        'military.employee.location',
        'parent_id',
        string='Sublocations'
    )
    parent_path = fields.Char(
        index=True,
        unaccent=False
    )
    complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name',
        recursive=True,
        store=True
    )
    address_id = fields.Many2one(
        'res.partner',
        required=False,
        string='Work Address',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    usage = fields.Selection([
        ('view', 'View'),
        ('internal', 'Internal'),
        ('external', 'External')
    ],
        string='Location Type',
        default='internal',
        index=True,
        required=True
    )
    status_id = fields.Many2one('military.employee.status')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive locations.'))

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = '%s / %s' % (
                    location.parent_id.complete_name, location.name)
            else:
                location.complete_name = location.name


class MilitaryEmployee(models.Model):
    _inherit = "military.employee"

    status_id = fields.Many2one('military.employee.status')
    location_id = fields.Many2one(
        'military.employee.location',
        "Employee Location",
        compute='_compute_last_move_id',
        readonly=True,
        store=True,
    )
    move_ids = fields.One2many(
        'military.employee.move.line',
        'employee_id',
        string='Employee Moves'
    )
    last_move_id = fields.Many2one(
        comodel_name='military.employee.move',
        compute='_compute_last_move_id',
        string='Last Move',
        store=True,
    )
    last_move_date = fields.Datetime(
        compute='_compute_last_move_id',
        string='Last Move Date',
        store=True,
    )

    @api.model
    def _compute_last_move_id(self):
        for employee in self:
            domain = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'done'),
            ]
            last_move_id = self.env['military.employee.move.line'].search(domain, limit=1, order='date desc')
            employee.last_move_id = last_move_id if last_move_id else False
            employee.last_move_date = last_move_id.date if last_move_id else False
            employee.location_id = last_move_id.location_dest_id if last_move_id else False
