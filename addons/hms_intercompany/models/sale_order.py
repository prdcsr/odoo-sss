from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    intercompany_toggle = fields.Boolean(string='Intercompany',default=True)
