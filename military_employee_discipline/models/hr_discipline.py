from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError


class HrDiscipline(models.Model):
    _name = "hr.discipline"
    _description = "Employee Discipline"
    _inherit = [
        "mail.thread",
        "tier.validation",
    ]

    name = fields.Char(
        string="# Document",
        required=True,
        default="/",
        copy=False,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="hr.discipline.type",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    reason_id = fields.Many2one(
        string="Reason",
        comodel_name="hr.discipline.reason",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    allowed_reason_ids = fields.Many2many(
        string="Allowed Reasons",
        comodel_name="hr.discipline.reason",
        compute="_compute_allowed_reason_ids",
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    department_id = fields.Many2one(
        string="Department",
        comodel_name="hr.department",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    effective_date = fields.Date(
        string="Effective Date",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self._default_company_id(),
    )
    state = fields.Selection(
        string="State",
        copy=False,
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("approve", "Approved"),
            ("open", "On Progress"),
            ("done", "Valid"),
            ("cancel", "Cancelled"),
        ],
        required=True,
        readonly=True,
        default="draft",
    )
    note = fields.Text(
        string="Note",
    )

