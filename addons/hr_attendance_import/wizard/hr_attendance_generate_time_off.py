from odoo import api, fields, models, sql_db, _
from odoo.tools.mimetypes import guess_mimetype
from datetime import datetime
from odoo.exceptions import UserError
import html2text
import logging

_logger = logging.getLogger(__name__)


class HrAttendanceGenerateTimeOff(models.TransientModel):
    _name = 'hr.attendance.generate.time.off'
    _inherit = 'hr.leave'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', readonly=True)

    @api.model
    def default_get(self, fields):
        result = super(HrAttendanceGenerateTimeOff, self).default_get(fields)
        if self.env.context.get('active_model') and self.env.context.get('active_id'):
            active_model = self.env.context.get('active_model')
            res_id = self.env.context.get('active_id')
            res_ids = self.env.context.get('active_ids')
            rec = self.env[active_model].browse(res_id)
            for attend in rec:
                result['employee_id'] = attend.employee_id.id
                result['payslip_status'] = True
                result['request_date_from'] = attend.check_in
                result['request_date_to'] = attend.check_out
                result['date_from'] = attend.check_in
                result['date_to'] = attend.check_out
                # self.date_from = attend.

        return result

    def create_time_off(self):
        for off in self:
            self.create(off)
        return {'type': 'ir.actions.act_window_close'}
