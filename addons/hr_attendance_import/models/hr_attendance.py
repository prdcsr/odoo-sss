from odoo import api, models, fields
import logging
import datetime
import pandas as pd

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    leave_id = fields.Many2one('hr.leave', string='Cuti')
    attendance_date = fields.Date(compute='_compute_attendance_date', store=True)
    is_late = fields.Char(compute='_compute_late_duration', string='Status Terlambat', store=True)
    information = fields.Char(string='Information')
    check_out_status = fields.Boolean(string='Check Out Status', compute='_compute_check_out_status', store=True)

    @api.depends('check_in')
    def _compute_attendance_date(self):
        for dat in self:
            dat.attendance_date = dat.check_in.date()

    # @api.depends('employee_id', 'check_out', 'worked_hours')
    # def _compute_food_salary(self):
    #     for each in self:
    #         each.food_salary = 0
    #         calendar = self.employee_id.resource_calendar_id
    #         week_days = calendar.attendance_ids
    #         check_in_day = pd.to_datetime(each.check_in).dayofweek
    #         # check_in_time = datetime.datetime.strptime(str(each.check_in), '%H:%M:%S')
    #         check_in_time = each.check_in.hour + each.check_in.minute / 60 + each.check_in.second / 3600
    #         today = each.check_in.date()
    #         leave_morning = self.env['hr.leave'].sudo().search([
    #             ('employee_id', '=', each.employee_id.id),
    #             ('date_from', '<=',
    #              datetime.datetime(year=today.year, month=today.month, day=today.day, hour=8, minute=0, second=0)),
    #             # production
    #             # datetime.datetime(year=today.year, month=today.month, day=today.day, hour=1, minute=0, second=0)), #Development
    #             ('date_to', '>=',
    #              datetime.datetime(year=today.year, month=today.month, day=today.day, hour=12, minute=0, second=0)),
    #             # production
    #             # datetime.datetime(year=today.year, month=today.month, day=today.day, hour=5, minute=0, second=0)), #development
    #             ('state', '=', 'validate')
    #         ])
    #         leave_afternoon = self.env['hr.leave'].sudo().search([
    #             ('employee_id', '=', each.employee_id.id),
    #             ('date_from', '<=',
    #              datetime.datetime(year=today.year, month=today.month, day=today.day, hour=13, minute=0, second=0)),
    #             # production
    #             # datetime.datetime(year=today.year, month=today.month, day=today.day, hour=6, minute=0, second=0)),
    #             ('date_to', '>=',
    #              datetime.datetime(year=today.year, month=today.month, day=today.day, hour=17, minute=0, second=0)),
    #             # production
    #             # datetime.datetime(year=today.year, month=today.month, day=today.day, hour=10, minute=0, second=0)), #development
    #             ('state', '=', 'validate')
    #         ])
    #
    #         if each.check_out:
    #             each.food_salary = each.employee_id.food_salary if each.employee_id.food_salary else 0
    #             food_salary = each.food_salary
    #
    #             for day in week_days:
    #                 if int(day.dayofweek) == check_in_day and day.day_period == 'morning':
    #                     if check_in_time > day.hour_from:
    #                         late_duration = check_in_time - day.hour_from
    #                         if (leave_morning or late_duration >= 0.083 or leave_afternoon) and each.check_out:
    #                             each.food_salary = food_salary / 2 if each.food_salary else 0
    #                         if each.worked_hours < 1:
    #                             each.food_salary = 0
    #                 # TODO: check if half day off

    @api.depends('check_in', 'employee_id')
    def _compute_late_duration(self):
        for each in self:
            check_in = each.check_in + datetime.timedelta(hours=7)
            check_in_day = pd.to_datetime(each.check_in).dayofweek
            # check_in_time = datetime.datetime.strptime(str(each.check_in), '%H:%M:%S')
            check_in_time = check_in.hour + check_in.minute / 60 + check_in.second / 3600
            calendar = self.employee_id.resource_calendar_id
            week_days = calendar.attendance_ids
            each.is_late = 'On Time'
            today = each.check_in.date()
            leave_morning = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', each.employee_id.id),
                ('date_from', '<=',
                 # datetime.datetime(year=today.year, month=today.month, day=today.day, hour=1, minute=0, second=0)),
                 datetime.datetime(year=today.year, month=today.month, day=today.day, hour=8, minute=0, second=0)),
                ('date_to', '>=',
                 # datetime.datetime(year=today.year, month=today.month, day=today.day, hour=5, minute=0, second=0)),
                 datetime.datetime(year=today.year, month=today.month, day=today.day, hour=12, minute=0, second=0)),
                ('state', '=', 'validate')
            ])

            for day in week_days:
                if int(day.dayofweek) == check_in_day and day.day_period == 'morning':
                    hour_from = day.hour_from
                    if check_in_time <= hour_from:
                        each.is_late = 'On Time'
                    else:
                        if not leave_morning and check_in_time < day.hour_to:
                            late_duration = check_in_time - day.hour_from
                            late_duration_sec = datetime.timedelta(hours=late_duration).seconds
                            mins, secs = divmod(late_duration_sec, 60)
                            hours, mins = divmod(mins, 60)
                            each.is_late = 'Terlambat Pagi ' + str(hours) + ' hour(s) ' + str(mins) + ' min(s) ' + str(
                                secs) + ' sec(s)'
                # TODO: check if half day off

                elif int(day.dayofweek) == check_in_day and day.day_period == 'afternoon':
                    if check_in_time <= day.hour_from:
                        each.is_late = 'On Time' if leave_morning else each.is_late
                        each.information = 'Cuti tanggal ' + str(leave_morning.date_from) + ' - ' + str(
                            leave_morning.date_to) if leave_morning else None
                    else:
                        late_duration = check_in_time - day.hour_from
                        late_duration_sec = datetime.timedelta(hours=late_duration).seconds
                        mins, secs = divmod(late_duration_sec, 60)
                        hours, mins = divmod(mins, 60)
                        each.is_late = 'Terlambat Siang ' + str(hours) + ' hour(s) ' + str(mins) + ' min(s) ' + str(
                            secs) + ' sec(s)'

    @api.depends('check_out', 'worked_hours')
    def _compute_check_out_status(self):
        for each in self:
            each.check_out_status = False
            if each.check_out and each.worked_hours > 1:
                each.check_out_status = True

    # def _compute_check_in_with_timezone(self):
    #     for each in self:
    #         user_tz = self.env.user.tz
    #         tz = pytz.timezone(user_tz)
    #         each.check_in = fields.Datetime.to_string(
    #             datetime.datetime.strptime(str(each.check_in), '%Y-%m-%d %H:%M:%S').astimezone(tz))

    # check_in = fields.Datetime(compute='_compute_check_in_with_timezone', store=True)
