from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError



#from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = "sale.order"

        
    def recompute_reward_lines(self):
        for order in self:
            #order._remove_invalid_reward_lines()
            order._create_new_no_code_reward_lines()
            #order._update_existing_reward_lines()

    def _create_new_no_code_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs:
            error_status = program._check_reward_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    continue
                elif program.reward_type == 'product' and program.reward_product_id.id not in self.order_line.mapped('product_id').ids:
                    self.write({'order_line': [(0, False, value) for value in self._get_new_reward_line_values(program)]})
                order.no_code_promo_program_ids |= program
    
    def _get_new_reward_line_values(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        return [self._get_new_reward_values_product(program)]
    
    def _get_new_reward_values_product(self, program):
        # Replace the logic to free product not discount
        
        #price_unit = self.order_line.filtered(lambda line: program.reward_product_id == line.product_id)[0].price_reduce

        order_lines = (self.order_line - self._get_reward_lines()).filtered(lambda x: program._is_valid_product(x.product_id))
        max_product_qty = sum(order_lines.mapped('product_uom_qty')) or 1
        # Remove needed quantity from reward quantity if same reward and rule product
        """if program._is_valid_product(program.reward_product_id):
            # number of times the program should be applied
            program_in_order = max_product_qty // (program.rule_min_quantity + program.reward_product_quantity)
            # multipled by the reward qty
            reward_product_qty = program.reward_product_quantity * program_in_order
        else:
            reward_product_qty = min(max_product_qty, self.order_line.filtered(lambda x: x.product_id == program.reward_product_id).product_uom_qty)
        reward_qty = min(int(int(max_product_qty / program.rule_min_quantity) * program.reward_product_quantity), reward_product_qty)"""

        reward_qty = int(int(max_product_qty / program.rule_min_quantity) * program.reward_product_quantity)
        # Take the default taxes on the reward product, mapped with the fiscal position
        taxes = program.reward_product_id.taxes_id
        if self.fiscal_position_id:
            taxes = self.fiscal_position_id.map_tax(taxes)
        return {
            'product_id': program.reward_product_id.id,
            'price_unit': -1,
            'product_uom_qty': reward_qty,
            'is_reward_line': True,
            'name': program.reward_product_id.name,
            'product_uom': program.reward_product_id.uom_id.id,
            'tax_id': [(4, tax.id, False) for tax in taxes],
        }
