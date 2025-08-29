from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        help="Default operating unit for this partner",
    )