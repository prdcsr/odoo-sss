from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    intercompany_account = fields.Many2one(
        'account.account',
        string='Intercompany Account',
    )
