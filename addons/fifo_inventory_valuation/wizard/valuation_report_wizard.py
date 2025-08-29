from odoo import models, fields, api
from datetime import datetime
import base64
import io
import xlsxwriter
import uuid


class InventoryValuationWizard(models.TransientModel):
    _name = 'fifo.inventory.valuation.wizard'
    _description = 'FIFO Inventory Valuation Wizard'

    date = fields.Date(string='Valuation Date', required=True, default=fields.Date.today())
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    line_ids = fields.One2many('fifo.inventory.valuation.line', 'wizard_id', string='Valuation Lines')
    export_file = fields.Binary("Excel File")
    export_filename = fields.Char("Excel Filename")
    include_child_locations = fields.Boolean("Include child locations", default=True)

    def action_calculate(self):
        self.ensure_one()
        StockMove = self.env['stock.move']
        Product = self.env['product.product']

        lines = []

        products = Product.search([('type', '=', 'product')])

        location_domain = (
            ('location_dest_id', 'child_of', self.location_id.id)
            if self.include_child_locations
            else ('location_dest_id', '=', self.location_id.id)
        )

        location_src_domain = (
            ('location_id', 'child_of', self.location_id.id)
            if self.include_child_locations
            else ('location_id', '=', self.location_id.id)
        )

        date = datetime(self.date.year, self.date.month, self.date.day, 23, 59, 59).strftime(
            '%Y-%m-%d %H:%M:%S')

        for product in products:
            # Get incoming moves
            incoming_moves = StockMove.search([
                ('product_id', '=', product.id),
                location_domain,
                # ('location_dest_id', '=', self.location_id.id),
                ('state', '=', 'done'),
                ('date', '<=', date)
            ], order='date asc')

            outgoing_moves = StockMove.search([
                ('product_id', '=', product.id),
                location_src_domain,
                # ('location_id', '=', self.location_id.id),
                ('state', '=', 'done'),
                ('date', '<=', date)
            ], order='date asc')

            layers = []
            for move in incoming_moves:
                layers.append({'qty': move.product_uom_qty, 'cost': move.price_unit})

            for move in outgoing_moves:
                qty_to_deduct = move.product_uom_qty
                while qty_to_deduct > 0 and layers:
                    if layers[0]['qty'] <= qty_to_deduct:
                        qty_to_deduct -= layers[0]['qty']
                        layers.pop(0)
                    else:
                        layers[0]['qty'] -= qty_to_deduct
                        qty_to_deduct = 0

            total_qty = sum(l['qty'] for l in layers)
            if total_qty > 0:
                avg_cost = sum(l['qty'] * l['cost'] for l in layers) / total_qty
                lines.append((0, 0, {
                    'product_id': product.id,
                    'quantity': total_qty,
                    'cost': avg_cost
                }))

        self.line_ids = [(5, 0, 0)] + lines
        return {
            'type': 'ir.actions.act_window',
            'name': 'FIFO Valuation',
            'res_model': 'fifo.inventory.valuation.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def action_export_excel(self):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Valuation')

        bold = workbook.add_format({'bold': True})
        sheet.write(0, 0, 'Product', bold)
        sheet.write(0, 1, 'Quantity', bold)
        sheet.write(0, 2, 'Unit Cost', bold)
        sheet.write(0, 3, 'Total Value', bold)

        row = 1
        for line in self.line_ids:
            sheet.write(row, 0, line.product_id.display_name)
            sheet.write(row, 1, round(line.quantity, 2))
            sheet.write(row, 2, round(line.cost, 2))
            sheet.write(row, 3, round(line.total_value, 2))
            row += 1

        workbook.close()
        output.seek(0)
        self.export_file = base64.b64encode(output.read())
        rand_uuid = uuid.uuid4()
        self.export_filename = f'{rand_uuid}_Location_Inventory_Valuation_{self.date}.xlsx'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fifo.inventory.valuation.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }
