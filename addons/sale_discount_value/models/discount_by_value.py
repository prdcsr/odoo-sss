# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import logging
import math
from decimal import Decimal, ROUND_HALF_UP

from odoo.tools import float_round


#_logger = logging.getLogger(__name__)


class PuthodOrderLines(models.Model):
    _inherit = 'sale.order.line'

    discount_value = fields.Float(string='Disc Price', digits=dp.get_precision('Discount'), default=0.0)

    #@api.one
    @api.constrains('discount_value', 'price_unit')
    def _check_active(self):
        for line in self:
            if line.price_unit > 0  and line.price_unit < line.discount_value:
                raise ValidationError(u"Attention Discount Bigger Then Price")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'discount_value')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        company = self.env.company
        currency = company.currency_id
        rounding_factor = Decimal(str(currency.rounding))  # Get the currency rounding factor

        for line in self:
            price = (line.price_unit - (line.discount_value/1.11)//1)
            price_discount =  price * (line.discount or 0.0) / 100.0

            price = float(Decimal(price-price_discount).quantize(0, ROUND_HALF_UP))

            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': math.floor(taxes['total_included'] - taxes['total_excluded']),
                'price_total': math.ceil(taxes['total_included']),
                'price_subtotal': taxes['total_excluded'],
                'price_reduce': price,
            })

    #@api.multi
    def _prepare_invoice_line(self):
        res = super(PuthodOrderLines, self)._prepare_invoice_line()
        # Not Transfer Line Note To Invoice
        """if self.display_type:
            res = []
            return res"""

        if self.price_reduce != 0:
            res['price_unit'] = self.price_reduce
            res['discount'] = 0
        
        return res


"""class AccountInvoice(models.Model):
    _inherit = "account.move"

    #@api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for move in self:
            for line in move.invoice_line_ids:
                price_unit = (line.price_unit - line.discount_value) * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids._origin.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
                for tax in taxes:
                    val = self._prepare_tax_line_vals(line, tax)
                    key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                    if key not in tax_grouped:
                        tax_grouped[key] = val
                    else:
                        tax_grouped[key]['amount'] += val['amount']
                        tax_grouped[key]['base'] += val['base']
            return tax_grouped


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    discount_value = fields.Float(string=u'Discount Price', digits=dp.get_precision('Discount'), default=0.0)

    #@api.one
    @api.constrains('discount_value', 'price_unit')
    def _check_active(self):
        for line in self: 
            if line.move_id.is_invoice(include_receipts=True) and line.price_unit < line.discount_value and line.discount_value != 0 :
                raise ValidationError("Attention Discount Lebih Besar Dari Harga!")

    #@api.one
    @api.depends('price_unit', 'discount', 'tax_ids', 'quantity',
        'product_id', 'move_id.partner_id', 'move_id.currency_id', 'move_id.company_id',
        'move_id.invoice_date', 'move_id.date', 'discount_value')
    def _compute_price(self):
        for rec in self:
            currency = rec.move_id and rec.move_id.currency_id or None
            price = (rec.price_unit - rec.discount_value) * (1 - (rec.discount or 0.0) / 100.0)
            taxes = False
            if rec.tax_ids:
                taxes = rec.tax_ids._origin.compute_all(price, currency, rec.quantity, product=rec.product_id, partner=rec.move_id.partner_id)
            rec.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else rec.quantity * price
            if rec.move_id.currency_id and rec.move_id.company_id and rec.move_id.currency_id != rec.move_id.company_id.currency_id:
                price_subtotal_signed = rec.movee_id.currency_id.with_context(date=rec.move_id._get_currency_rate_date()).compute(price_subtotal_signed, rec.move_id.company_id.currency_id)
            sign = rec.move_id.type in ['in_refund', 'out_refund'] and -1 or 1
            rec.price_subtotal_signed = price_subtotal_signed * sign
    
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        
        if self.discount_value != 0:
            price_unit = price_unit - self.discount_value or 0.00
        return super(AccountMoveLine, self)._get_price_total_and_subtotal_model(
            price_unit, quantity, discount, currency, product, partner, taxes, move_type
        )"""
