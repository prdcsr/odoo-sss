from collections import defaultdict
from datetime import timedelta

from odoo import models, fields, api


class FoodCostReportWizard(models.TransientModel):
    _name = 'food.cost.report.wizard'
    _description = 'Food Cost Report Wizard'

    warehouse_id = fields.Many2one('stock.warehouse', required=True)
    start_date = fields.Date(required=True, string='Start Date')
    end_date = fields.Date(required=True, string='End Date')

    def _get_highlighted_products(self):
        tmpl_ids = self.env['product.template'].search([('is_highlighted', '=', True)]).ids
        return self.env['product.product'].search([('product_tmpl_id', 'in', tmpl_ids)])

    def _get_date_range(self):
        if not self.start_date or not self.end_date:
            return []
        return [self.start_date + timedelta(days=i)
                for i in range((self.end_date - self.start_date).days + 1)]

    def _get_line_map(self):
        products = self._get_highlighted_products()
        date_range = self._get_date_range()

        aml_domain = [
            ('product_id', 'in', products.ids),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('move_id.state', '=', 'posted'),
            ('account_id', '=', 91),
        ]
        move_lines = self.env['account.move.line'].search(aml_domain)

        line_map = defaultdict(lambda: {'qty': 0.0, 'value': 0.0})
        for line in move_lines:
            key = f"{line.product_id.id}_{line.date.strftime('%Y-%m-%d')}"
            line_map[key]['qty'] += line.quantity
            line_map[key]['value'] += line.balance
        return dict(line_map)

    def action_view_qweb_table(self):
        return self.env.ref('foodcost_table_report.report_food_cost_table_action').report_action(self)
