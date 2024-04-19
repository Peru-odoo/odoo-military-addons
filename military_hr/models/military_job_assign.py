from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, AccessError, UserError


# ToDo:
# Add job verification procedures:
#     - job should be available for assignment (filter)
#     - verify on assignment that job expected employee is >= 0


class MilitaryJobAssign(models.Model):
    _name = "military.job.assign"
    _inherit = ["mail.thread"]
    _description = "Employee Job Assignment"
    _rec_name = "complete_name"
    _check_company_auto = True
    _order = "date desc"

    name = fields.Char(
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
        default="Noname"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
    ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        default='draft',
        tracking=3)
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
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        default=lambda self: self.env.company.partner_id)
    assign_line = fields.One2many(
        'military.job.assign.line',
        'assign_id',
        string='Assignment Lines',
        states={'done': [('readonly', True)],
                'confirm': [('readonly', True)]},
        copy=True,
        auto_join=True
    )
    employee_ids = fields.Many2many(
        'military.job.assign.line',
        'employee_id')
    description = fields.Text('Description')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        default=lambda self: self.env.company
    )
    origin = fields.Char(
        'Basis',
        index=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Basis of the assign"
    )

    @api.depends("name", "partner_id", "date")
    def _compute_complete_name(self):
        for rec in self:
            name = rec.name if rec.name else ''
            partner = rec.partner_id.name if rec.partner_id else ''
            date = rec.date.strftime("%d.%m.%Y") if rec.date else ''
            rec.complete_name = "Наказ %s від %s №%s" % (partner, date, name)

    def effective_date_in_past(self):
        for assign in self:
            if assign.date > fields.Date.today():
                raise UserError(
                    _(
                        "Assignment date should be before today!"
                    )
                )
        return True

    def unlink(self):

        if not self.env.context.get("force_delete", False):
            for assign in self:
                if assign.state not in ["draft", "cancel"]:
                    raise UserError(
                        _(
                            "Unable to Delete Assignment!\n"
                            "Assignment has been initiated. Either cancel the assign or\n"
                            "create another assign to undo it."
                        )
                    )
        return super(MilitaryJobAssign, self).unlink()

    def action_done(self):
        self.ensure_one()
        has_permission = self._check_permission_group("military_job.group_military_job_assign")
        if has_permission and self.effective_date_in_past():
            self.state_done()
        else:
            self.write({"state": "done"})

    def action_confirm(self):
        self.ensure_one()
        has_permission = self._check_permission_group("military_job.group_military_job_assign")
        if has_permission:
            self.state_confirm()

    def action_cancel(self):
        self.ensure_one()
        has_permission = self._check_permission_group(
            "military_job.group_military_job_assign"
        )
        if has_permission:
            self.write({"state": "cancel"})

    def action_draft(self):
        self.ensure_one()
        has_permission = self._check_permission_group(
            "military_job.group_military_job_assign"
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

    def state_done(self):
        today = fields.Date.today()
        for assign in self:
            if assign.date <= today:
                for assign_line in assign.assign_line:
                    assign_line.employee_id.job_id = assign_line.dst_job_id
                assign.state = "done"
            else:
                raise UserError(
                    _(
                        "Assignment date should be before today!"
                    )
                )
        return True

    def signal_confirm(self):
        for assign in self:
            if (
                    self.user_has_groups("military_job.group_military_job_assign")
                    and assign.effective_date_in_past()
            ):
                assign.state = "confirm"
            else:
                assign.state_confirm()
        return True


class MilitaryJobAssignLine(models.Model):
    _name = "military.job.assign.line"
    _description = "Employee Assignment Line"
    _inherit = "mail.thread"
    _rec_name = "date"
    _check_company_auto = True

    assign_id = fields.Many2one(
        'military.job.assign',
        string='Assignment Reference',
        required=True,
        ondelete='cascade',
        index=True, copy=False
    )
    assign_partner_id = fields.Many2one(
        related='assign_id.partner_id',
        store=True,
        string='Customer',
        readonly=False
    )
    state = fields.Selection(
        related='assign_id.state',
        string='Assignment Status',
        readonly=True,
        copy=False,
        store=True,
    )
    # TODO add temporary job option
    temp = fields.Boolean("Temporary Job", default=False)
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="military.employee",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    description = fields.Text(string='Description')
    src_job_id = fields.Many2one(
        string="From Job",
        comodel_name="military.job",
        compute="_compute_onchange_employee",
        store=True,
        readonly=True,
        check_company=True,
    )
    src_department_id = fields.Many2one(
        "military.department",
        string="From Department",
        compute="_compute_onchange_employee",
        store=True,
        readonly=True,
    )
    dst_job_id = fields.Many2one(
        "military.job",
        string="Destination Job",
        readonly=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
    )
    dst_department_id = fields.Many2one(
        "military.department",
        string="Destination Department",
        # related="dst_job_id.department_id",
        store=True,
        required=True,
        check_company=True,
    )
    date = fields.Date(
        string="Effective Date",
        related="assign_id.date",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        store=True,
        readonly=True,
    )
    origin = fields.Char(
        'Basis',
        index=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Basis of the assign"
    )

    @api.onchange("dst_job_id")
    def _onchange_dst_job(self):
        if self.dst_job_id:
            self.dst_department_id = self.dst_job_id.department_id
        else:
            ""

    @api.depends("employee_id")
    def _compute_onchange_employee(self):
        for assign in self:
            if assign.employee_id:
                assign.src_job_id = assign.employee_id.job_id
                assign.src_department_id = assign.employee_id.department_id
            else:
                assign.src_job_id = False
                assign.src_department_id = False

    # @api.model
    # def create(self, values):
    #     # Check if expected_employees is >= 0
    #     if 'dst_job_id' in values and values.get('dst_job_id'):
    #         destination_job = self.env['military.job'].browse(values['dst_job_id'])
    #         new_expected_employees = values.get('new_expected_employees',
    #                                             destination_job.expected_employees)
    #         if new_expected_employees < 0:
    #             raise ValidationError(
    #                 "Expected Employees for the destination job must be greater than or equal to 0.")
    #
    #     # Check if employee_id is used only once in assign
    #     employee_id = values.get('employee_id')
    #     if employee_id:
    #         existing_assign_lines = self.search([('employee_id', '=', employee_id)])
    #         if existing_assign_lines:
    #             raise ValidationError("An employee can only be assignred once.")
    #
    #     return super(HrTransferLine, self).create(values)
    #
    def write(self, values):

        # Check if employee_id is used only once in assign
        employee_id = values.get('employee_id', self.employee_id.id)
        existing_assign_lines = self.search(
            [('employee_id', '=', employee_id), ('id', '!=', self.id)])
        if existing_assign_lines:
            raise ValidationError("An employee can only be assignred once.")

        return super(MilitaryJobAssignLine, self).write(values)


class MilitaryEmployee(models.Model):
    _inherit = 'military.employee'

    job_assign_id = fields.Many2one(
        comodel_name='military.job.assign',
        compute='_compute_assign_id',
        string='Job Assignment',
        readonly=True,
        store=True,
    )
    job_assign_date = fields.Date(
        related='job_assign_id.date',
        string='Job Assignment Date',
        store=True,
    )

    @api.depends('job_id')
    def _compute_assign_id(self):
        for employee in self:
            domain = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'done'),
            ]
            job_assign_id = self.env['military.job.assign.line'].search(domain, limit=1,
                                                                        order='date desc')
            employee.job_assign_id = job_assign_id.assign_id
