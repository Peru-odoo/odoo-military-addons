from odoo import fields, models


class HrDisciplineReason(models.Model):
    _name = "hr.discipline.reason"
    _description = "Dicipline Reason"

    name = fields.Char(
        string="Discipline Reason",
        required=True,
    )
    dicipline_type_id = fields.Many2one(
        string="Discipline Type",
        comodel_name="hr.discipline.type",
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
