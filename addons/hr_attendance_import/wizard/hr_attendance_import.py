from odoo import models, fields
import logging
import os
import base64
import pandas as pd
import numpy as np
import duckdb
import datetime

_logger = logging.getLogger(__name__)


class HrAttendancenImport(models.TransientModel):
    _name = 'attendance.import.form'
    attendance_file = fields.Binary('File')

    def act_import(self):
        decoded = base64.b64decode(self.attendance_file)
        path = '/var/lib/odoo/.local/share/Odoo/filestore'  #production
        # path = ''  # development

        with open(path + 'attendance.xls', 'wb') as f:
            f.write(decoded)

        df = pd.read_excel(path + 'attendance.xls')  # production
        # df = pd.read_excel('attendance.xls')

        df['date'] = pd.to_datetime(df['Date And Time']).dt.date
        df['time'] = pd.to_datetime(df['Date And Time']).dt.time
        df['name'] = np.where(df['Last Name'].isnull(), df['First Name'], df['First Name'] + ' ' + df['Last Name'])
        df['personnel_id'] = df['Personnel ID']

        query = """
                  select
                    name,
                    personnel_id,
                    date,
                    date + min(time) as check_in,
                    date + max(time) as check_out,
                  from df
                  group by name, date, personnel_id
                """

        new_df = duckdb.query(query).df()

        new_df['check_in'] = pd.to_datetime(new_df['check_in'])
        # new_df['check_out'] = new_df['check_out'].values.astype("float64")
        new_df['date'] = pd.to_datetime(new_df['date']).dt.date
        new_df['check_in_day'] = pd.to_datetime(new_df['check_in']).dt.dayofweek

        new_df['check_out'] = pd.to_datetime(new_df['check_out'])
        new_df = new_df.dropna()

        for index, row in new_df.iterrows():
            department = self.env['hr.department'].search([('name', '=', 'Unit')])
            employee = self.env['hr.employee'].search([
                ('zk_teco_id', '=', row['personnel_id']),
                ('department_id', '=', department.id)
            ])

            if employee:

                vals = {
                    'employee_id': employee.id,
                    'check_in': row['check_in'] - datetime.timedelta(hours=7),
                    'check_out': None if pd.isnull(row['check_out']) else row['check_out'] - datetime.timedelta(
                        hours=7),
                    'check_out_status': True,
                }

                calendar = employee.resource_calendar_id
                week_days = calendar.attendance_ids
                check_in_day = row['check_in_day']
                check_in = row['check_in']
                check_out = row['check_out']
                check_out_time = check_out.hour + check_out.minute / 60 + check_out.second / 3600
                check_in_time = check_in.hour + check_in.minute / 60 + check_in.second / 3600

                date_check = datetime.date(year=check_in.year, month=check_in.month, day=check_in.day)
                # out_check = datetime.datetime(year=check_in.year, month=check_in.month, day=check_in.day)
                attendance_check = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('attendance_date', '=', date_check),
                ])

                # if attendance_check:
                #     vals = attendance_check

                # TODO: GET VARIABLE TO CHECK HALF DAY OFF
                check_in_date = check_in.date()
                leave_afternoon = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('date_from', '<=',
                     datetime.datetime(year=check_in_date.year, month=check_in_date.month, day=check_in_date.day,
                                       hour=13, minute=0, second=0)),
                    # development
                    ('date_to', '>=',
                     datetime.datetime(year=check_in_date.year, month=check_in_date.month,
                                       day=check_in_date.day,
                                       hour=17, minute=0, second=0)),  # development
                    ('state', '=', 'validate')
                ])

                for day in week_days:
                    if int(day.dayofweek) == check_in_day and day.day_period == 'morning':
                        if leave_afternoon and check_out_time < day.hour_to:
                            vals['check_out_status'] = False

                        late_duration = check_in_time - day.hour_from
                        late_duration_sec = datetime.timedelta(hours=late_duration).seconds

                    elif int(day.dayofweek) == check_in_day and day.day_period == 'afternoon':
                        if not leave_afternoon and check_out_time < day.hour_to:
                            vals['check_out_status'] = False

                if attendance_check:
                    attendance_check.write({
                        'check_in': vals['check_in'],
                        'check_out': vals['check_out'],
                        'check_out_status': vals['check_out_status']
                    })
                else:
                    self.env['hr.attendance'].create(vals)

        os.remove(path + 'attendance.xls')  # production

        return {'type': 'ir.actions.act_window_close'}
