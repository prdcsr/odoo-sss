from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class Company(models.Model):
    _name = 'uom.uom'
    _inherit = 'uom.uom'

    coretax_code = fields.Char(string='Coretax Code')