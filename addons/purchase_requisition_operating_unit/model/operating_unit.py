# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class OperatingUnit(models.Model):
    _inherit = "operating.unit"

    purchase_requisition_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Purchase Agreement Sequence",
        help="Sequence of Purchase Agreemnt with this operating unit",
    )
