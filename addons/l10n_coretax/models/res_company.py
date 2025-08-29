from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class Company(models.Model):
    _inherit = 'res.company'

    nitku_num = fields.Char(string='NITKU', size=6, default="000000")
    vat16 = fields.Char(string='VAT16', size=16, default="0000000000000000")