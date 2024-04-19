import logging, datetime

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class MilitaryEmployee(models.Model):
    _name = "military.employee"
    _rec_name = "complete_name"
    _description = "Employee"
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _mail_post_access = 'read'
    _avoid_quick_create = True

    name = fields.Char(
        string="Employee Name",
        store=True,
        readonly=True,
        tracking=True
    )
    user_id = fields.Many2one(
        'res.users',
        'User',
        store=True,
        readonly=False
    )
    user_partner_id = fields.Many2one(
        related='user_id.partner_id',
        related_sudo=False,
        string="User's partner"
    )
    active = fields.Boolean(
        'Active',
        default=True,
        store=True,
        readonly=False
    )
    company_id = fields.Many2one(
        'res.company',
        required=True)
    last_name = fields.Char(
        "Last Name",
        required=True,
        tracking=True
    )
    first_name = fields.Char(
        "First Name",
        required=True,
        tracking=True
    )
    middle_name = fields.Char(
        "Middle Name",
        required=True,
        tracking=True)
    name_gent = fields.Char(
        string="Name Genitive",
        # compute="_get_declension",
        help="Name in genitive declension (Whom/What)",
        store=True
    )
    name_datv = fields.Char(
        string="Name Dative",
        # compute="_get_declension",
        help="Name in dative declension (for Whom/ for What)",
        store=True
    )
    name_ablt = fields.Char(
        string="Name Ablative",
        # compute="_get_declension",
        help="Name in ablative declension (by Whom/ by What)",
        store=True
    )
    service_type = fields.Selection([
        ('mobilised', 'Mobilised'),
        ('contract', 'Contract'),
        ('regular', 'Regular'),
    ],
        string='Service Type',
        default='mobilised',
        required=True,
        help="The personell service type")

    callsign = fields.Char()
    complete_name = fields.Char(
        "Complete Name",
        compute="_compute_complete_name",
        store=True,
        readonly=True,
        default="Noname"
    )
    job_id = fields.Many2one(
        'military.job',
        string='Job Position',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    job_title = fields.Char(
        "Job Title",
        related="job_id.complete_name",
        store=True
    )
    department_id = fields.Many2one(
        related="job_id.department_id",
        store=True,
        # readonly=True
    )
    parent_id = fields.Many2one(
        related="department_id.manager_id",
        store=True,
        readonly=True
    )
    conscription_place = fields.Many2one(
        "res.partner",
        "Conscription Place",
        tracking=True
    )
    conscription_date = fields.Date(
        "Conscription Date",
        tracking=True
    )
    age = fields.Integer(
        string="Age",
        compute='_compute_age'
    )
    blood_type_ab = fields.Selection(
        string="Blood Type (ABO)",
        selection=[
            ("a", "A"),
            ("b", "B"),
            ("ab", "AB"),
            ("o", "O"),
        ],
    )
    blood_type_rh = fields.Selection(
        string="Blood Type (Rh)",
        selection=[
            ("+", "+"),
            ("-", "-"),
        ],
    )
    country_id = fields.Many2one(
        'res.country',
        'Nationality (Country)',
        groups="military_hr.military_hr_user",
        tracking=True
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups="military_hr.military_hr_user",
        tracking=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups="military_hr.military_hr_user", default='single', tracking=True)
    spouse_complete_name = fields.Char(string="Spouse Complete Name", groups="military_hr.military_hr_user",
                                       tracking=True)
    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups="military_hr.military_hr_user",
                                   tracking=True)
    children = fields.Integer(string='Number of Dependent Children', groups="military_hr.military_hr_user",
                              tracking=True)
    certificate = fields.Selection([
        ('graduate', 'Graduate'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('doctor', 'Doctor'),
        ('other', 'Other'),
    ], 'Certificate Level', default='other', groups="military_hr.military_hr_user", tracking=True)
    study_field = fields.Char("Field of Study", groups="military_hr.military_hr_user", tracking=True)
    study_school = fields.Char("School", groups="military_hr.military_hr_user", tracking=True)
    place_of_birth = fields.Char('Place of Birth', groups="military_hr.military_hr_user", tracking=True)
    country_of_birth = fields.Many2one(
        'res.country',
        string="Country of Birth",
        groups="military_hr.military_hr_user",
        tracking=True)
    birthday = fields.Date(
        'Date of Birth',
        groups="military_hr.military_hr_user",
        tracking=True
    )
    identification_id = fields.Char(
        string='Identification No',
        groups="military_hr.military_hr_user",
        tracking=True)
    passport_id = fields.Char(
        'Passport No',
        groups="military_hr.military_hr_user",
        tracking=True
    )
    additional_note = fields.Text(string='Additional Note', groups="military_hr.military_hr_user",
                                  tracking=True)
    mobile_phone = fields.Char(
        'Mobile',
        store=True,
    )
    status_id = fields.Many2one('hr.employee.status')
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
            last_move_id = self.env['hr.move.line'].search(domain, limit=1, order='date desc')
            employee.last_move_id = last_move_id if last_move_id else False
            employee.last_move_date = last_move_id.date if last_move_id else False
            employee.location_id = last_move_id.location_dest_id if last_move_id else False

    @api.model
    def _get_complete_name(self, rank_id, name, job_title):
        job = job_title[0].lower() + job_title[1:] if job_title else ''
        return " ".join(p for p in (rank_id.name, name, job) if p)

    @api.depends("rank_id", "name", "job_id.complete_name", "job_title")
    def _compute_complete_name(self):
        for rec in self:
            rec.complete_name = rec._get_complete_name(rec.rank_id, rec.name, rec.job_title)

    @api.depends("birthday")
    def _compute_age(self):
        for rec in self:
            rec.age = relativedelta(datetime.date.today(), rec.birthday).years

    @api.depends('name', 'first_name', 'middle_name', 'last_name')
    def _get_declension(self):
        declension_ua_model = self.env['declension.ua']
        grammatical_cases = ['gent', 'datv', 'ablt']
        for record in self:
            inflected_fields = declension_ua_model.get_declension_fields(record, grammatical_cases)
            for field, value in inflected_fields.items():
                setattr(record, field, value.title())

    @api.model
    def _get_name(self, last_name, first_name, middle_name):
        return " ".join(p for p in (last_name, first_name, middle_name) if p)

    @api.onchange("job_id")
    def _onchange_job(self):
        if self.job_id:
            self.department_id = self.job_id.department_id
        else:
            self.department_id = None

    @api.onchange("last_name", "first_name", "middle_name", "name", "rank_id", "job_title")
    def _onchange(self):
        self.name = self._get_name(self.last_name, self.first_name, self.middle_name)
        self.complete_name = self._get_complete_name(self.rank_id, self.name, self.job_title)

    def _prepare_vals(self, vals):
        res = []
        if not vals.get("name"):
            last_name = vals.get("last_name", self.last_name)
            first_name = vals.get("first_name", self.first_name)
            middle_name = vals.get("middle_name", self.middle_name)
            vals["name"] = self._get_name(last_name, first_name, middle_name)
        if not vals.get("complete_name"):
            name = vals.get("name", self.name)
            job_title = vals.get("job_title", self.job_title)
            vals["complete_name"] = self._get_complete_name(self.rank_id, name, job_title)
        if not vals.get("parent_id"):
            vals["parent_id"] = self.department_id.manager_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._prepare_vals(vals)
        res = super().create(vals_list)
        return res

    def write(self, vals):
        self._prepare_vals(vals)
        res = super().write(vals)
        return res
