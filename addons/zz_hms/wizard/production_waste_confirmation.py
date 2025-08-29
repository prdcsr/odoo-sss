from odoo import models, fields, api


class TimeWarningWizard(models.TransientModel):
    _name = 'stock.picking.time.warning.wizard'
    _description = 'Time-based Operation Warning Wizard'

    picking_id = fields.Many2one('stock.picking', required=True)
    operation_type = fields.Char('Operation Type', readonly=True)

    def action_confirm(self):
        """Proceed with validation after user confirms"""
        self.picking_id.with_context(from_time_warning_wizard=True).button_validate()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel the validation"""
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking_id = self.env.context.get('default_picking_id')
        operation_type = self.env.context.get('default_operation_type')

        if picking_id:
            res.update({
                'picking_id': picking_id,
                'operation_type': operation_type,
            })

        return res