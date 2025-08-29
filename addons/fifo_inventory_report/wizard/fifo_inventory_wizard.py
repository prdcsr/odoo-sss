from odoo import models, fields, api
from datetime import datetime

class FIFOInventoryReportWizard(models.TransientModel):
    _name = 'fifo.inventory.report.wizard'
    _description = 'FIFO Inventory Report Wizard'

    date = fields.Datetime(string='Valuation Date')
    location_id = fields.Many2one('stock.location', string='Location')
    include_child_locations = fields.Boolean(string='Include Child Locations', default=True)
    show_details = fields.Boolean(string='Show Detailed Operation', default=False)

    report_line_ids = fields.One2many('fifo.inventory.report.line', 'wizard_id', string='Report Lines')

    def action_generate_html(self):
        # Dummy: should calculate FIFO valuation here
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fifo.inventory.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_export_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/fifo_inventory_report/download/excel',
            'target': 'self',
        }