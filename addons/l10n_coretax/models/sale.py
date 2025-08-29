from odoo import models, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.partner_id and not self.partner_id.validated_identity:
            return {
                'warning': {
                    'title': "Validation Warning",
                    'message': "The identity of the selected partner is not validated!",
                }
            }

    # @api.model
    # def create(self, vals):
    #     if vals.get('partner_id'):
    #         partner = self.env['res.partner'].browse(vals['partner_id'])
    #         if not partner.validated_identity:
    #             raise UserError("The identity of the partner isn't validated. Please validate it before proceeding.")
    #
    #     return super(SaleOrder, self).create(vals)


    # def action_confirm(self):
    #     for order in self:
    #         if not order.partner_id.validated_identity:
    #             raise UserError("The identity of the partner isn't validated. Order confirmation is not allowed.")
    #
    #     return super(SaleOrder, self).action_confirm()
