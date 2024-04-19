from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class MilitaryDepartment(models.Model):
    _name = "military.department"
    _description = "Department"
    _inherit = ['mail.thread']
    _rec_name = 'complete_name'
    _parent_store = True
    _order = "level, sequence, name"
    _avoid_quick_create = True

    sequence = fields.Integer(default=1)
    name = fields.Char('Department Name', required=True)
    complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name',
        recursive=True,
        store=True
    )
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company)
    parent_id = fields.Many2one(
        'military.department',
        string='Parent Department',
        index=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    child_ids = fields.One2many(
        'military.department',
        'parent_id',
        string='Child Departments'
    )
    job_ids = fields.One2many(
        'military.job',
        compute='_compute_job_ids',
        string='Jobs',
        recursive=True,
    )
    member_ids = fields.One2many(
        comodel_name='military.employee',
        compute='_compute_member_ids',
        string='Members',
        recursive=True,
    )
    manager_id = fields.Many2one(
        'military.employee',
        string='Manager',
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    note = fields.Text('Note')
    parent_path = fields.Char(index=True, unaccent=False)
    master_department_id = fields.Many2one(
        'military.department',
        'Master Department',
        compute='_compute_master_department_id',
        store=True
    )
    code = fields.Char(
        string="Code",
        compute="_department_code",
        store=True,
        readonly=False
    )
    level = fields.Integer(
        string="Level",
        compute="_compute_level",
        store=True,
        recursive=True
    )
    commandor_id = fields.Many2one(
        'military.job',
        string='Commandor',
        tracking=True,
    )
    name_gent = fields.Char(
        string="Name Genitive",
        compute="_get_declension",
        help="Name in genitive declension (Whom/What)",
        store=True)
    name_datv = fields.Char(
        string="Name Dative",
        compute="_get_declension",
        help="Name in dative declension (for Whom/for What)",
        store=True
    )
    name_ablt = fields.Char(
        string="Name Ablative",
        compute="_get_declension",
        help="Name in ablative declension (by Whom/by What)",
        store=True
    )
    complete_name_gent = fields.Char(
        "Complete Name Genitive",
        compute="_compute_complete_name_gent",
        store=True,
        recursive=True
    )

    @api.model
    def _compute_member_ids(self):
        for department in self:
            employees = self.env['military.employee'].search([
                '|',
                ('department_id', '=', department.id),
                ('department_id', 'child_of', department.id),
            ])
            department.member_ids = employees

    @api.model
    def _compute_child_ids(self):
        return self.env['military.department'].search([('id', 'child_of', self.ids)])

    @api.model
    def _compute_job_ids(self):
        for department in self:
            jobs = self.env['military.job'].search([
                '|',
                ('department_id', '=', department.id),
                ('department_id', 'child_of', department.id),
            ])
            department.job_ids = jobs

    @api.depends("level", "parent_id.level")
    def _compute_level(self):
        for dep in self:
            dep.level = dep.level
            if dep.parent_id:
                dep.level = dep.parent_id.level + 1
            else:
                dep.level = 1

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    def name_get(self):
        res = []
        for dep in self:
            if dep.code:
                name = "[%s] %s" % (dep.code, dep.complete_name.upper())
            else:
                name = dep.complete_name.upper()
            res.append((dep.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", "=ilike", name + "%"), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        departments = self.search(domain + args, limit=limit)
        return departments.name_get()

    @api.depends("parent_id", "code")
    def _department_code(self):
        for dep in self:
            dep.code = dep.code
            if not dep.code:
                dep.code = dep.parent_id.code
            else:
                dep.code = dep.code

    @api.depends("name", "name_gent", "parent_id.complete_name_gent",
                 "company_id.name_gent")
    def _compute_complete_name(self):
        for dep in self:
            if dep.parent_id and dep.parent_id.complete_name_gent:
                dep.complete_name = "%s %s" % (dep.name,
                                               dep.parent_id.complete_name_gent)
            else:
                dep.complete_name = "%s %s" % (dep.name, dep.company_id.name_gent)

    @api.depends("name_gent",
                 "parent_id.complete_name_gent",
                 "company_id.name_gent")
    def _compute_complete_name_gent(self):
        for dep in self:
            if not dep.name_gent:
                if not dep.parent_id:
                    dep.complete_name_gent = dep.name_gent
                else:
                    dep.complete_name_gent = dep.parent_id.complete_name_gent
            else:
                if dep.parent_id and dep.parent_id.complete_name_gent:
                    dep.complete_name_gent = "%s %s" % (
                        dep.name_gent,
                        dep.parent_id.complete_name_gent)
                else:
                    dep.complete_name_gent = "%s %s" % (dep.name_gent,
                                                        dep.company_id.name_gent)

    @api.onchange("name", "name_gent", "parent_id")
    def _onchange_department_name(self):
        if self.name or self.parent_id or self.name_gent:
            self._compute_complete_name()
            self._compute_complete_name_gent()
            self._department_code()

    @api.depends('name')
    def _get_declension(self):
        declension_ua_model = self.env['declension.ua']
        grammatical_cases = ['gent', 'datv', 'ablt']
        for record in self:
            inflected_fields = declension_ua_model.get_declension_fields(record, grammatical_cases)
            for field, value in inflected_fields.items():
                setattr(record, field, value)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive departments.'))
    
    @api.depends('parent_path')
    def _compute_master_department_id(self):
        for department in self:
            department.master_department_id = int(department.parent_path.split('/')[0])
    
    @api.model_create_multi
    def create(self, vals_list):
        # TDE note: auto-subscription of manager done by hand, because currently
        # the tracking allows to track+subscribe fields linked to a res.user record
        # An update of the limited behavior should come, but not currently done.
        departments = super(MilitaryDepartment, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        for department, vals in zip(departments, vals_list):
            manager = self.env['military.employee'].browse(vals.get("manager_id"))
            if manager.user_id:
                department.message_subscribe(partner_ids=manager.user_id.partner_id.ids)
        return departments

    def write(self, vals):
        """ If updating manager of a department, we need to update all the employees
            of department hierarchy, and subscribe the new manager.
        """
        # TDE note: auto-subscription of manager done by hand, because currently
        # the tracking allows to track+subscribe fields linked to a res.user record
        # An update of the limited behavior should come, but not currently done.
        if 'manager_id' in vals:
            manager_id = vals.get("manager_id")
            if manager_id:
                manager = self.env['military.employee'].browse(manager_id)
                # subscribe the manager user
                if manager.user_id:
                    self.message_subscribe(partner_ids=manager.user_id.partner_id.ids)
            # set the employees's parent to the new manager
            self._update_employee_manager(manager_id)
        return super(MilitaryDepartment, self).write(vals)
    
    
class MilitaryEmployee(models.Model):
    _inherit = "military.employee"

    department_level = fields.Integer('Level', store='True', related='department_id.level')
