from calendar import monthrange
from collections import defaultdict
from datetime import datetime, timedelta

from odoo import fields, models

class InventoryComparisonReportWizard(models.TransientModel):
    _name = 'inventory.comparison.wizard'
    _description = 'Inventory Comparison Report Wizard'

    report_date = fields.Date(string="Report Date", default=fields.Date.context_today)
    file_name = fields.Char("File Name")
    file_data = fields.Binary("Excel File")

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        required=True,
        help="Filter inventory comparison for this specific warehouse"
    )

    def action_export_excel(self):

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_inventory_excel_report?wizard_id=%s' % self.id,
            'target': 'self',
        }
    def _get_inventory_comparison(self):
        self.ensure_one()
        warehouse = self.warehouse_id
        warehouse_location = warehouse.view_location_id.id
        report_date = self.report_date
        year = report_date.year
        month = report_date.month

        internal_locations = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('id', 'child_of', warehouse_location)
        ])
        quants = self.env['stock.quant'].search([
            ('location_id', 'in', internal_locations.ids),
        ])
        inventories = self.env['stock.inventory'].search([
            ('location_ids', 'in', internal_locations.ids),
            ('date', '=', report_date),
            ('state', 'in', ['done'])
        ],limit=2)
        inventory_lines = self.env['stock.inventory.line'].search([
            ('inventory_id', 'in', inventories.id),
        ])
        data = defaultdict(lambda: {
            'account': '',
            'product': None,
            'code': '',
            'on_hand': 0,
            'counted': 0,
            'uom': '',
            'cost': 0.0
        })
        account = ''
        if warehouse.name == "ALAM SUTRA" or "ALAM SUTERA":
            account = "MAS"
        if warehouse.name == "GADING SERPONG":
            account = "MGS"
        if warehouse.name == "BINTARO":
            account = "MBO"

        for quant in quants:
            pid = quant.product_id.id
            product = quant.product_id

            data[pid]['account'] = account
            data[pid]['product'] = product.name
            data[pid]['code'] = product.default_code or ''
            data[pid]['on_hand'] += quant.quantity
            data[pid]['cost'] = product.standard_price
            data[pid]['uom'] = product.uom_id.name

        for line in inventory_lines:
            pid = line.product_id.id
            product = line.product_id

            data[pid]['product'] = product.name
            data[pid]['code'] = product.default_code or ''
            data[pid]['counted'] += line.product_qty

        return list(data.values())



