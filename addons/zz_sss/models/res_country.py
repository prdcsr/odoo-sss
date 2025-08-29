from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class Company(models.Model):
    _name = 'res.country'
    _inherit = 'res.country'

    coretax_country_code = fields.Char(string='Coretax Country Code')