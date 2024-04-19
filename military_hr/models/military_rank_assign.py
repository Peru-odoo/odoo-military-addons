from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class RankAssign(models.Model):
    _name = "rank.assign"
    _inherit = "mail.thread"
    _description = "Rank Assign"
    _rec_name = "complete_name"
    _check_company_auto = True

    number = fields.Char(
        "Order Number",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    complete_name = fields.Char(
        "Complete Name",
        compute="_compute_complete_name",
        store=True,
        tracking=True,
        default="Noname")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('done', 'Done')],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default='draft'
    )
    date = fields.Date(
        string='Date',
        required=True,
        readonly=True,
        index=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        default=fields.Date.today,
        help="Date of assign"
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Order Author',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
        change_default=True,
        index=True,
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        store=True,
        readonly=True,
    )
    assign_line = fields.One2many(
        'rank.assign.line', 'assign_id',
        string='Assign Lines',
        states={'cancel': [('readonly', True)],
                'confirm': [('readonly', True)]},
        copy=True, auto_join=True)
    description = fields.Text('Description')

    @api.depends("number", "partner_id", "date")
    def _compute_complete_name(self):
        for rec in self:
            number = rec.number if rec.number else ''
            partner = rec.partner_id.name if rec.partner_id else ''
            date = rec.date.strftime("%d.%m.%Y") if rec.date else ''
            rec.complete_name = "Наказ %s від %s №%s" % (partner, date, number)

    def effective_date_in_future(self):

        for assign in self:
            if assign.date >= fields.Date.today():
                return False
        return True

    def unlink(self):
        if not self.env.context.get("force_delete", False):
            for assign in self:
                if assign.state not in ["draft"]:
                    raise UserError(
                        _(
                            "Unable to Delete Assign!\n"
                            "Assign has been initiated. Either cancel the assign or\n"
                            "create another assign to undo it."
                        )
                    )
        return super(RankAssign, self).unlink()

    def action_assign(self):
        self.ensure_one()
        has_permission = self._check_permission_group(
            "military_rank.group_rank_assign"
        )
        if has_permission and not self.effective_date_in_future():
            self.state_done()
        else:
            self.write({"state": "confirm"})

    def action_confirm(self):
        self.ensure_one()
        has_permission = self._check_permission_group(
            "military_rank.group_rank_assign"
        )
        if has_permission:
            self.signal_confirm()

    def action_cancel(self):
        self.ensure_one()
        has_permission = self._check_permission_group(
            "military_rank.group_rank_assign"
        )
        if has_permission:
            self.write({"state": "cancel"})

    def action_draft(self):
        self.ensure_one()
        has_permission = self._check_permission_group(
            "military_rank.group_rank_assign"
        )
        if has_permission:
            self.write({"state": "draft"})

    def _check_permission_group(self, group=None):
        for assign in self:
            if group and not assign.user_has_groups(group):
                raise AccessError(
                    _("You don't have the access rights to take this action.")
                )
            else:
                continue
        return True

    def state_confirm(self):
        for assign in self:
            assign.state = "confirm"
        return True

    def signal_confirm(self):
        for assign in self:
            if (
                    self.user_has_groups("military_rank.group_rank_assign")
                    and assign.effective_date_in_future()
            ):
                assign.state = "confirm"
            else:
                assign.state_confirm()
        return True

    def state_done(self):
        today = fields.Date.today()
        for assign in self:
            if assign.date <= today:
                assign.assign_line.employee_id.rank_id = assign.assign_line.dst_rank
                assign.state = "done"
                # assign.assign_line.state = "done"
            else:
                return False
        return True


class RankAssignLine(models.Model):
    _name = "rank.assign.line"
    _inherit = ["mail.thread"]
    _description = "Rank Assign Line"
    _rec_name = "date"
    _check_company_auto = True

    assign_id = fields.Many2one(
        'rank.assign',
        string='Assign Reference',
        required=True,
        ondelete='cascade',
        index=True, copy=False)
    assign_partner_id = fields.Many2one(
        related='assign_id.partner_id',
        store=True,
        string='Customer',
        readonly=False
    )
    date = fields.Date(
        string="Effective Date",
        related="assign_id.date",
        store=True,
    )
    state = fields.Selection(string="State", related="assign_id.state")
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        store=True,
        readonly=True,
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="military.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    src_rank = fields.Many2one(
        string="From Rank",
        comodel_name="military.rank",
        compute="_compute_rank",
        store=True,
        readonly=True
    )
    dst_rank = fields.Many2one(
        string="Destination Rank",
        comodel_name="military.rank",
        store=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.depends("employee_id")
    def _compute_rank(self):
        if self.employee_id.rank_id:
            self.src_rank = self.employee_id.rank_id
        else:
            self.src_rank = False

    @api.onchange("employee_id")
    def _onchange_employee(self):
        if self.employee_id:
            self.src_rank = self.employee_id.rank_id
            self.dst_rank = self.employee_id.rank_id.parent_id
        else:
            self.src_rank = False
            self.dst_rank = False


class MilitaryEmployee(models.Model):
    _inherit = 'military.employee'

    rank_assign_id = fields.Many2one(
        comodel_name='rank.assign',
        compute='_compute_rank_assign_id',
        string='Rank Assign',
        readonly=True,
        store=True,
    )
    rank_assign_date = fields.Date(
        related='rank_assign_id.date',
        string='Rank Assign Date',
        store=True,
    )

    @api.depends('rank_id')
    def _compute_rank_assign_id(self):
        for employee in self:
            domain = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'done'),
            ]
            rank_assign_id = self.env['rank.assign.line'].search(domain, limit=1,
                                                                 order='date desc')
            employee.rank_assign_id = rank_assign_id.assign_id
