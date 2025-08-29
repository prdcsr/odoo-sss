from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import pytz


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for rec in self:
            if not self._context.get('skip_foodcost_check'):
                # Existing validation for SO KITCHEN HARIAN and STOCK OPNAME ECER
                if rec.picking_type_id.name in ['SO KITCHEN HARIAN'] and not self.env.context.get(
                        'from_validation_wizard'):
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'stock.picking.validation.confirmation.wizard',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'new',
                        'context': {
                            'default_picking_id': rec.id,
                        },
                    }

                # New time-based validation for Production and Waste
                if rec.picking_type_id.name in ['Production', 'Waste'] and not self.env.context.get(
                        'from_time_warning_wizard'):
                    # Get current time in user's timezone (GMT+7)
                    user_tz = pytz.timezone(self.env.user.tz or 'Asia/Jakarta')  # Default to Jakarta timezone
                    utc_now = datetime.now(pytz.UTC)
                    local_time = utc_now.astimezone(user_tz).time()
                    warning_time = datetime.strptime('21:30', '%H:%M').time()  # 9:30 PM

                    show_warning = False
                    # Waste: Show warning during day hours (before 9:30 PM)
                    # Production: Show warning during night hours (9:30 PM onwards until next morning)
                    if rec.picking_type_id.name == 'Waste' and local_time < warning_time:
                        show_warning = True
                    elif rec.picking_type_id.name == 'Production' and (
                            local_time >= warning_time or local_time < datetime.strptime('06:00', '%H:%M').time()):
                        show_warning = True

                    if show_warning:
                        return {
                            'type': 'ir.actions.act_window',
                            'res_model': 'stock.picking.time.warning.wizard',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'target': 'new',
                            'context': {
                                'default_picking_id': rec.id,
                                'default_operation_type': rec.picking_type_id.name,
                            },
                        }

        return super().button_validate()