from odoo import fields, models

class PartnerPointHistory(models.Model):
    _name = 'partner.point.history'

    point = fields.Float('Point')
    ref_code = fields.Char("Reference Code")
    partner_id = fields.Many2one('res.partner', string='Partner')
    loyalty_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program')