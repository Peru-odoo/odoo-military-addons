from odoo import fields, models


class HrDisciplineType(models.Model):
    _name = "hr.discipline.type"
    _description = "Discipline Type"

    name = fields.Char(
        string="Discipline Type",
        required=True,
    )
    code = fields.Char(
        string="Code",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    note = fields.Text(string="Note")
    reason_ids = fields.One2many(
        string="Discipline Reason",
        comodel_name="hr.discipline.reason",
        inverse_name="discipline_type_id",
    )
    sequence_id = fields.Many2one(
        string="Sequence",
        comodel_name="ir.sequence",
        ondelete="set null",
        company_dependent=True,
    )
