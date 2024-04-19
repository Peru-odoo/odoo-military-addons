from odoo import api, fields, models


class HrMove(models.Model):
    _name = "hr.move"
    _description = "Staff Move"
    _rec_names_search = ['name', 'employee_id.name']
    _inherit = "mail.thread"
    _order = "id desc"

    name = fields.Char(
        'Number',
        copy=False,
    )
    origin = fields.Char(
        'Basis',
        index=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Basis of the movement"
    )
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ],
        string='Status',
        compute='_compute_state',
        default='draft',
        copy=False,
        index=True,
        readonly=True,
        store=True,
        tracking=True,
    )
    date = fields.Date(
        'Move Date',
        default=fields.Date.today(),
        index=True,
        tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
    )
    location_id = fields.Many2one(
        'hr.work.location', "Destination Location",
        # default=lambda self: self.env['hr.move.type'].browse(
        #     self._context.get('default_move_type_id')).location_id,
        readonly=True,
        required=True,
        states={'draft': [('readonly', False)]}
    )
    move_line_ids = fields.One2many(
        'hr.move.line',
        'move_id',
        'Operations',
        copy=True
    )
    move_type_id = fields.Many2one(
        'hr.move.type',
        'Move Type',
        required=True,
        readonly=False,
        states={'draft': [('readonly', False)]}
    )
    move_type_code = fields.Selection(
        related='move_type_id.code',
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        'Partner',
        check_company=True,
        states={'done': [('readonly', True)],
                'cancel': [('readonly', True)]}
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True,
        store=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        'Responsible',
        tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        default=lambda self: self.env.user)
    owner_id = fields.Many2one(
        'res.partner',
        'Assign Owner',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        check_company=True,
        help="When validating the transfer, the products will be assigned to this owner.")
    employee_ids = fields.Many2one(
        'hr.employee',
        'Employee',
        related='move_line_ids.employee_id',
        readonly=True
    )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for move in self:
            move_id = isinstance(move.id, int) and move.id or getattr(move, '_origin',
                                                                      False) and move._origin.id
            if move_id:
                moves = self.env['hr.move.line'].search([('move_id', '=', move_id)])
                for move in moves:
                    move.write({'partner_id': move.partner_id.id})

    @api.onchange('move_type_id')
    def onchange_move_type_id(self):
        for move in self:
            move.location_id = move.move_type_id.location_id
