from odoo import fields, models, api, _
from odoo.addons.web_editor.controllers.main import handle_history_divergence


class MilitaryJob(models.Model):
    _name = "military.job"
    _description = "Military Job"
    _inherit = "mail.thread"
    _display_name = "complete_name"
    _order = "level, sequence"
    _avoid_quick_create = True

    active = fields.Boolean(
        'Active',
        default=True,
        store=True,
        readonly=False
    )
    sequence = fields.Integer(default=1)
    level = fields.Integer(
        'Level',
        store='True',
        related='department_id.level'
    )
    name = fields.Char(
        string='Job Position',
        required=True,
        index='trigram',
        translate=False
    )
    name_gent = fields.Char(
        string="Name Genitive",
        compute="_get_declension",
        help="Name in genitive declension (Whom / What)",
        store=True)
    name_datv = fields.Char(
        string="Name Dative",
        compute="_get_declension",
        help="Name in dative declension (for Whom / for What)",
        store=True)
    name_ablt = fields.Char(
        string="Name Ablative",
        compute="_get_declension",
        help="Name in ablative declension (by Whom / by What)",
        store=True)

    @api.depends('name')
    def _get_declension(self):
        declension_ua_model = self.env['declension.ua']
        grammatical_cases = ['gent', 'datv', 'ablt']
        for record in self:
            inflected_fields = declension_ua_model.get_declension_fields(record, grammatical_cases)
            for field, value in inflected_fields.items():
                setattr(record, field, value)

    complete_name = fields.Char(
        string='Job Name',
        store='True',
        compute='_compute_complete_name',
        readonly='False'
    )
    complete_name_gent = fields.Char(
        string="Complete Name Genitive",
        compute="_compute_complete_name_declension",
        help="Name in genitive declension (Whom / What)",
        store=True
    )
    complete_name_datv = fields.Char(
        string="Complete Name Dative",
        compute="_compute_complete_name_declension",
        help="Name in dative declension (for Whom / for What)",
        store=True
    )
    complete_name_ablt = fields.Char(
        string="Complete Name Ablative",
        compute="_compute_complete_name_declension",
        help="Name in ablative declension (by Whom / by What)",
        store=True
    )
    mos = fields.Char(string="Job MOS code")
    payroll_grade = fields.Char(string="Payroll Grade")
    employee_id = fields.Many2one(
        'military.employee',
        string='Employees',
        groups='base.group_user'
    )
    description = fields.Html(string='Job Description', sanitize_attributes=False)
    requirements = fields.Text('Requirements')
    department_id = fields.Many2one(
        'military.department',
        string='Department',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # _sql_constraints = [
    #     ('name_company_uniq', 'unique(name, mos, company_id, department_id)',
    #      'The name of the job position and MOS must be unique per department in company!'),
    # ]

    @api.depends("name", "department_id.complete_name_gent", "company_id.name_gent")
    def _compute_complete_name(self):
        for job in self:
            job.complete_name = job.name
            if job.name and job.department_id.complete_name_gent:
                job.complete_name = '%s %s' % (job.name, job.department_id.complete_name_gent)
            else:
                job.complete_name = '%s %s' % (job.name, job.company_id.name_gent)

    @api.depends("name", "department_id.complete_name_gent", "company_id.name_gent")
    def _compute_complete_name_declension(self):
        for job in self:
            job.complete_name_gent = job.name_gent
            job.complete_name_datv = job.name_datv
            job.complete_name_ablt = job.name_ablt
            if job.name:
                job.complete_name_gent = '%s %s' % (
                    job.name_gent, job.department_id.complete_name_gent)
                job.complete_name_datv = '%s %s' % (
                    job.name_datv, job.department_id.complete_name_gent)
                job.complete_name_ablt = '%s %s' % (
                    job.name_ablt, job.department_id.complete_name_gent)

    @api.onchange('name', 'department_id')
    def _onchange_name(self):
        if self.name or self.department_id:
            self._compute_complete_name()
            self._compute_complete_name_declension()

    def name_get(self):
        res = []
        for job in self:
            name = job.complete_name
            res.append((job.id, name))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """ We don't want the current user to be follower of all created job """
        return super(MilitaryJob, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(MilitaryJob, self).copy(default=default)

    def write(self, vals):
        if len(self) == 1:
            handle_history_divergence(self, 'description', vals)
        return super(MilitaryJob, self).write(vals)


class MilitaryEmployee(models.Model):
    _inherit = 'military.employee'

    def _job_count(self):
        for each in self:
            job_ids = self.env['military.job.assign.line'].sudo().search(
                [('employee_id', '=', each.id)])
            each.job_count = len(job_ids)

    def job_view(self):
        self.ensure_one()
        domain = [
            ('employee_id', '=', self.id)]
        return {
            'name': _('Jobs'),
            'domain': domain,
            'res_model': 'military.assign.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree',
            'limit': 80,
            'context': "{'employee_id': %s}" % self.id
        }

    job_count = fields.Integer(compute='_job_count',
                               string='# Jobs')
