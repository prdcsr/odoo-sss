from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class Company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    nitku_num = fields.Char(string='NITKU', size=6, default="000000")