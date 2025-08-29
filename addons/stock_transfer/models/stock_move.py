from odoo import api, fields, models, SUPERUSER_ID, _
class Picking(models.Model):
    _inherit = "stock.move"
