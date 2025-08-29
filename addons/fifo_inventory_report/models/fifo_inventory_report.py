from odoo import models, fields, api
from odoo.tools.float_utils import float_round

class FIFOInventoryReportLine(models.TransientModel):
    _name = 'fifo.inventory.report.line'
    _description = 'FIFO Inventory Report Line'

    wizard_id = fields.Many2one('fifo.inventory.report.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('uom.uom', string='UoM')
    quantity = fields.Float(string='Quantity')
    value = fields.Float(string='Value')
    location_id = fields.Many2one('stock.location', string='Location')
    date = fields.Datetime(string='Date')
    operations = fields.Text(string='Operations')