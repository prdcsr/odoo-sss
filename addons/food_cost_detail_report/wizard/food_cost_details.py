from collections import defaultdict
from datetime import timedelta

from odoo import models, fields, api

class FoodCostDetailReportWizard(models.TransientModel):
    _name = 'food.cost.detail.report.wizard'
    _description = 'Food Cost Detail Report Wizard'

    warehouse_id = fields.Many2one('stock.warehouse', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    report_date = fields.Date(
        required=True,
        string='Report Date',
        default=lambda self: fields.Date.today() - timedelta(days=1)
    )

    line_ids = fields.One2many('food.cost.detail.report.line', 'wizard_id', string='Report Lines')

    @api.onchange('warehouse_id', 'product_id', 'report_date')
    def _onchange_refresh_lines(self):
        if not (self.product_id and self.report_date):
            self.line_ids = [(5, 0, 0)]
            return
        analytic_account = 0
        if self.warehouse_id.name in ["ALAM SUTRA","ALAM SUTERA"]:
            analytic_account = 2
        elif self.warehouse_id.name == "GADING SERPONG":
            analytic_account = 3
        elif self.warehouse_id.name == "BINTARO":
            analytic_account = 1

        aml_domain = [
            ('product_id', '=', self.product_id.id),
            ('date', '=', self.report_date),
            ('move_id.state', '=', 'posted'),
            ('account_id', '=', 91),
            ('analytic_account_id', '=', analytic_account),
        ]
        move_lines = self.env['account.move.line'].search(aml_domain)

        lines = []
        for line in move_lines:
            lines.append((0, 0, {
                'date': line.date,
                'description': line.name,
                'balance': line.balance,
                'quantity': line.quantity,
                'uom_name': line.product_uom_id.name if line.product_uom_id else '',
            }))
        self.line_ids = [(5, 0, 0)] + lines


class FoodCostDetailReportLine(models.TransientModel):
    _name = 'food.cost.detail.report.line'
    _description = 'Food Cost Detail Report Line'

    wizard_id = fields.Many2one('food.cost.detail.report.wizard', required=True, ondelete='cascade')

    date = fields.Date()
    description = fields.Char()
    balance = fields.Float()
    quantity = fields.Float()
    uom_name = fields.Char(string="UoM")
