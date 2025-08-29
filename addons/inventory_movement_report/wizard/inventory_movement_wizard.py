from collections import defaultdict
from datetime import datetime, timedelta

from odoo import fields, models
import base64
import io
import xlsxwriter

class StockCardReportWizard(models.TransientModel):
    _name = 'inventory.movement.wizard'
    _description = 'Inventory Movement Report Wizard'

    report_date = fields.Date(string="Report Date", default=fields.Date.context_today)
    file_name = fields.Char("File Name")
    file_data = fields.Binary("Excel File")

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse",
        required=True,
        help="Filter inventory movement for this specific warehouse"
    )

    def action_export_excel(self):

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_inventory_excel_report?wizard_id=%s' % self.id,
            'target': 'self',
        }
        # self.ensure_one()
        #
        # data = self._get_inventory_movements()
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # worksheet = workbook.add_worksheet("Inventory Report")
        #
        # # Headers
        # headers = ['Product', 'UoM', 'Closing Stock (Yesterday)', 'Stock In (Today)', 'Stock Out (Today)']
        # for col, header in enumerate(headers):
        #     worksheet.write(0, col, header)
        #
        # # Data rows
        # for row, line in enumerate(data, start=1):
        #     worksheet.write(row, 0, line['product'].display_name)
        #     worksheet.write(row, 1, line['product'].uom_id.name or '')
        #     worksheet.write(row, 2, line['closing'])
        #     worksheet.write(row, 3, line['in'])
        #     worksheet.write(row, 4, line['out'])
        #
        # workbook.close()
        # output.seek(0)
        # xlsx_data = output.read()
        #
        # self.file_data = base64.b64encode(xlsx_data)
        # self.file_name = f"Inventory_Movement_{self.report_date}.xlsx"
        #
        # # Open download form
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'inventory.movement.wizard',
        #     'res_id': self.id,
        #     'view_mode': 'form',
        #     'target': 'new',
        # }

    def _get_inventory_movements(self):
        self.ensure_one()
        Product = self.env['product.product']
        StockMoveLine = self.env['stock.move.line']

        report_date = self.report_date
        date_start = datetime.combine(report_date, datetime.min.time())
        date_end = datetime.combine(report_date, datetime.max.time())
        closing_date = date_start - timedelta(seconds=1)

        # Internal locations in selected warehouse
        warehouse = self.warehouse_id
        internal_locations = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('id', 'child_of', warehouse.view_location_id.id)
        ])
        internal_location_ids = internal_locations.ids

        data = defaultdict(lambda: {'product': None, 'closing': 0, 'in': 0, 'out': 0})

        done_moves = StockMoveLine.search([
            ('state', '=', 'done'),
            ('date', '<=', date_end),
            '|',
            ('location_id', 'in', internal_location_ids),
            ('location_dest_id', 'in', internal_location_ids),
        ])

        for line in done_moves:
            product = line.product_id
            pid = product.id

            if product.type == 'product' and ("KITCHEN" in product.categ_id.complete_name):
                if not data[pid]['product']:
                    data[pid]['product'] = product

                move_date = fields.Datetime.from_string(line.date)

                qty = line.qty_done
                src_internal = line.location_id.id in internal_location_ids
                dest_internal = line.location_dest_id.id in internal_location_ids

                if move_date <= closing_date:
                    if dest_internal and not src_internal:
                        data[pid]['closing'] += qty
                    elif src_internal and not dest_internal:
                        data[pid]['closing'] -= qty
                elif date_start <= move_date <= date_end:
                    if dest_internal and not src_internal:
                        data[pid]['in'] += qty
                    elif src_internal and not dest_internal:
                        data[pid]['out'] += qty

        return list(data.values())

    def action_view_report(self):
        return self.env.ref('inventory_movement_report.inventory_movement_report_action').report_action(self)

    def action_print_pdf(self):
        return self.env.ref('inventory_movement_report.inventory_movement_report_pdf').report_action(self)