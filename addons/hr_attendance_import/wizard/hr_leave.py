from odoo import api, fields, models, sql_db, _
import datetime
import logging
from collections import namedtuple
import math

_logger = logging.getLogger(__name__)

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


class HrAttendanceGenerateTimeOff(models.TransientModel):
    _name = 'hr.leave.wizard'
    _inherit = 'hr.leave'

    @api.model
    def default_get(self, fields):
        result = super(HrAttendanceGenerateTimeOff, self).default_get(fields)
        if self.env.context.get('active_model') and self.env.context.get('active_id'):
            active_model = self.env.context.get('active_model')
            res_id = self.env.context.get('active_id')
            res_ids = self.env.context.get('active_ids')
            recs = self.env[active_model].browse(res_ids)
            recs = sorted(recs, key=lambda rec: rec['check_in'] + datetime.timedelta(hours=7))

            # for attend in recs:
            if recs:
                result['employee_id'] = recs[0].employee_id.id
                result['department_id'] = recs[0].employee_id.department_id.id
                result['payslip_status'] = True
                result['request_date_from'] = recs[0].check_in + datetime.timedelta(hours=7)
                result['request_date_to'] = recs[len(recs) - 1].check_out + datetime.timedelta(hours=7)
                result['date_from'] = recs[0].check_in
                result['date_to'] = recs[len(recs) - 1].check_out + datetime.timedelta(hours=7)
                # self.date_from = attend.

        return result

    def create_time_off(self):
        for dat in self:
            item = {
                'holiday_type': dat.holiday_type,
                'holiday_status_id': dat.holiday_status_id.id,
                'date_from': dat.date_from - datetime.timedelta(hours=7),
                'date_to': dat.date_to - datetime.timedelta(hours=7),
                'request_date_from': dat.request_date_from - datetime.timedelta(hours=7),
                'request_date_to': dat.request_date_to - datetime.timedelta(hours=7),
                'request_date_from_period': dat.request_date_from_period,
                'employee_id': dat.employee_id.id,
                'request_unit_half': dat.request_unit_half,
                'request_unit_hours': dat.request_unit_hours,
                'request_unit_custom': dat.request_unit_custom,
                'request_hour_from': dat.request_hour_from,
                'request_hour_to': dat.request_hour_to,
                'number_of_days': dat.number_of_days,
                'name': dat.name,
                'mode_company_id': dat.mode_company_id.id,
                'category_id': dat.category_id.id,
                'department_id': dat.department_id.id,
                'payslip_status': dat.payslip_status,
                # 'report_note': dat.report_note,
                'message_attachment_count': dat.message_attachment_count
            }
            dat.unlink()
            self.env['hr.leave'].create([item])
            # time_off = self.create([dict(dat)])
            # attendances = self.env['hr.attendance'].search([
            #     ('employee_id', '=',dat.employee_id),
            #     ('check_in', '>=', time_off.date_from),
            #     ('check_out', '<=', time_off.date_to),
            # ])
            #
            # for attend in attendances:
            #     if attend.worked_hours < 8 or attend.is_late or not attend.check_out_status:
            #         attend.write({
            #             'leave_id': time_off.id
            #         })
        return {'type': 'ir.actions.act_window_close'}
