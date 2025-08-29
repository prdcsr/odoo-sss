from odoo import api, fields, models, sql_db, _
import datetime
import logging
from collections import namedtuple
import math

_logger = logging.getLogger(__name__)


class HrAttendanceGenerateTimeOff(models.TransientModel):
    _name = 'hr.overtime.wizard'
    _inherit = 'hr.overtime'

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
                check_in = recs[0].check_in + datetime.timedelta(hours=7)
                date = check_in.day
                month = check_in.month
                year = check_in.year
                result['employee_id'] = recs[0].employee_id.id
                result['department_id'] = recs[0].employee_id.department_id.id
                result['date_from'] = datetime.datetime(year=year, month=month, day=date, hour=10, minute=0, second=0)
                result['date_to'] = recs[len(recs) - 1].check_out
                # self.date_from = attend.

        return result

    def create_overtime(self):
        for dat in self:
            item = {
                'employee_id': dat.employee_id.id,
                'name': dat.name,
                'department_id': dat.department_id.id,
                'job_id': dat.job_id.id,
                'manager_id': dat.manager_id.id,
                'overtime_officer_id': dat.overtime_officer_id.id,
                'current_user': dat.current_user.id,
                'current_user_boolean': dat.current_user_boolean,
                'project_id': dat.project_id.id,
                'project_manager_id': dat.project_manager_id.id,
                'contract_id': dat.contract_id.id,
                'date_from': dat.date_from,
                'date_to': dat.date_to,
                'days_no_tmp': dat.days_no_tmp,
                'days_no': dat.days_no,
                'desc': dat.desc,
            }
            dat.unlink()
            overtime = self.env['hr.overtime'].create(item)
            overtime.submit_to_f()
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
