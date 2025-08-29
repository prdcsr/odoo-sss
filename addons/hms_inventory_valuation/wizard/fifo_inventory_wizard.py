from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import io
import base64
import xlsxwriter


class FifoInventoryValuationWizard(models.TransientModel):
    _name = 'fifo.inventory.valuation.wizard'
    _description = 'FIFO Inventory Valuation Wizard'

    valuation_date = fields.Date(string='Valuation Date', default=fields.Date.context_today, required=True)
    location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')])
    include_child = fields.Boolean(string='Include Child Locations', default=True)
    show_detailed_operation = fields.Boolean(string='Show Detailed Operation')

    @api.onchange('location_id')
    def _onchange_location_id(self):
        self.include_child = bool(self.location_id)

    def _get_locations(self):
        if self.location_id:
            if self.include_child:
                return self.location_id.search([('id', 'child_of', self.location_id.id)])
            return self.location_id
        return self.env['stock.location'].search([('usage', '=', 'internal')])

    def _compute_fifo_value(self):
        StockValuationLayer = self.env['stock.valuation.layer']
        locations = self._get_locations().ids
        layers = StockValuationLayer.search([
            ('create_date', '<=', self.valuation_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            ('product_id.categ_id', '!=', 22),
            ('product_id.type', '=', 'product'),
            '|',
            ('location_dest_id', 'in', locations),
            ('location_id', 'in', locations),
        ], order='create_date asc')

        fifo_data = {}
        fifo_queue = {}
        detailed = {}

        for layer in layers:
            product = layer.product_id
            product_id = str(product.id)
            qty = layer.quantity
            value = layer.value

            if product_id not in fifo_queue:
                fifo_queue[product_id] = []
                fifo_data[product_id] = {
                    'product_id': product.id,
                    'product_code': product.default_code or '',
                    'product_name': product.name,
                    'uom': product.uom_id.name,
                    'qty': 0.0,
                    'value': 0.0
                }
                detailed[product_id] = []

            # Inbound (positive qty)
            if qty > 0 and layer.location_dest_id.id in locations:
                fifo_queue[product_id].append({
                    'qty': qty,
                    'unit_cost': value / qty if qty else 0.0,
                    'value': value,
                    'picking': layer.stock_move_id.picking_id.name or '',
                    'uom': product.uom_id.name,
                })
                fifo_data[product_id]['qty'] += qty
                fifo_data[product_id]['value'] += value
                if self.show_detailed_operation:
                    detailed[product_id].append({
                        'picking': layer.stock_move_id.picking_id.name or '',
                        'qty': qty,
                        'uom': product.uom_id.name,
                        'unit_cost': value / qty if qty else 0.0,
                        'total_cost': value,
                    })

            # Outbound (negative qty)
            elif qty < 0 and layer.location_id.id in locations:
                remaining_qty = abs(qty)
                fifo_data[product_id]['qty'] += qty  # subtract qty (qty is negative)
                fifo_data[product_id]['value'] += value  # subtract value

                if self.show_detailed_operation:
                    detailed[product_id].append({
                        'picking': layer.stock_move_id.picking_id.name or '',
                        'qty': qty,
                        'uom': product.uom_id.name,
                        'unit_cost': value / qty if qty else 0.0,
                        'total_cost': value,
                    })

                # Consume from FIFO queue
                while remaining_qty > 0 and fifo_queue[product_id]:
                    entry = fifo_queue[product_id][0]
                    if entry['qty'] <= remaining_qty:
                        remaining_qty -= entry['qty']
                        fifo_queue[product_id].pop(0)
                    else:
                        entry['qty'] -= remaining_qty
                        remaining_qty = 0

        # Only keep remaining stock (positive qty)
        final = {}
        final_detailed = {}
        for pid, queue in fifo_queue.items():
            total_qty = sum(l['qty'] for l in queue)
            total_val = sum(l['qty'] * l['unit_cost'] for l in queue)
            if total_qty > 0:
                final[pid] = fifo_data[pid]
                final[pid]['qty'] = total_qty
                final[pid]['value'] = total_val
                if self.show_detailed_operation:
                    final_detailed[pid] = detailed[pid]

        return final, final_detailed

    def action_view_report(self):
        grouped, detailed = self._compute_fifo_value()
        return self.env.ref('hms_inventory_valuation.action_fifo_inventory_report').report_action(self, data={
            'grouped': grouped,
            'detailed': detailed,
            'show_details': self.show_detailed_operation,
            'date': self.valuation_date.strftime('%Y-%m-%d'),
        })

    def action_export_excel(self):
        grouped, _ = self._compute_fifo_value()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('FIFO Valuation')

        bold = workbook.add_format({'bold': True})
        sheet.write(0, 0, 'Product Code', bold)
        sheet.write(0, 1, 'Product Name', bold)
        sheet.write(0, 2, 'UoM', bold)
        sheet.write(0, 3, 'Qty', bold)
        sheet.write(0, 4, 'Value', bold)

        row = 1
        for key, line in grouped.items():
            sheet.write(row, 0, line['product_code'])
            sheet.write(row, 1, line['product_name'])
            sheet.write(row, 2, line['uom'])
            sheet.write(row, 3, line['qty'])
            sheet.write(row, 4, line['value'])
            row += 1

        workbook.close()
        output.seek(0)
        export_id = self.env['ir.attachment'].create({
            'name': f'FIFO_Inventory_Valuation_{self.valuation_date}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
        })
        output.close()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{export_id.id}?download=true',
            'target': 'new',
        }