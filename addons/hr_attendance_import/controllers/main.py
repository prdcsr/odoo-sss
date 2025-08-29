import uuid

import pandas as pd
import requests
import xlsxwriter

from odoo import api, http
from xlrd import open_workbook
import pandas as pd
import numpy as np
import base64
import os
import duckdb
import datetime
import pytz
from odoo import api, fields, models
import logging
import mimetypes
import calendar
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
import io

_logger = logging.getLogger(__name__)


class HrAttendanceImport(http.Controller):

    @api.model
    @http.route('/hr_attendance/import', auth='user', type='http', website=False, csrf=False)
    def attendance_import(self, file):
        data = file.read()
        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)
        # path = '/var/lib/odoo/.local/share/Odoo/filestore'  #production
        path = ''  # development

        try:
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

            for index, row in new_df.iterrows():
                employee = http.request.env['hr.employee'].search([
                    '|',
                    ('name', '=', row['name']),
                    ('zk_teco_id', '=', row['personnel_id'])
                ])

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

                # TODO: GET VARIABLE TO CHECK HALF DAY OFF
                check_in_date = check_in.date()
                leave_afternoon = http.request.env['hr.leave'].sudo().search([
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

                http.request.env['hr.attendance'].create(vals)

            os.remove(path + 'attendance.xls')  # production
            # os.remove('attendance.xls')
            return 'Success'
        except Exception as e:
            raise UserWarning(e)

    @api.model
    @http.route('/hr_attendance/import/solution', auth='user', type='http', website=False, csrf=False)
    def solution_attendance_import(self, file):
        data = file.read()
        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)
        # path = '/var/lib/odoo/.local/share/Odoo/filestore'  #production
        path = ''  # development

        try:
            with open(path + 'solution_attendance.xls', 'wb') as f:
                f.write(decoded)

            df = pd.read_excel(path + 'solution_attendance.xls')

            df['name'] = df['Nama']
            df['id'] = df['No. ID']
            df['check_in'] = np.where(df['Scan Masuk'].isnull(), np.NaN, df['Tanggal'] + ' ' + df['Scan Masuk'])
            df['check_in'] = pd.to_datetime(df['check_in'])

            df['check_out'] = np.where(df['Scan Pulang'].isnull(), np.NaN, df['Tanggal'] + ' ' + df['Scan Pulang'])
            df['check_out'] = pd.to_datetime(df['check_out'])
            df.dropna(subset=['check_in'], inplace=True)

            for index, row in df.iterrows():
                department = http.request.env['hr.department'].search([('name', '=', row['department'])])
                employees = http.request.env['hr.employee'].search([
                    ('zk_teco_id', '=', row['id']),
                    ('department_id', '=', department[0].id)
                ])

                for emp in employees:
                    if emp.department_id.name == row['Department']:
                        calendar = emp.resource_calendar_id
                        week_days = calendar.attendance_ids
                        check_in_day = row['Tanggal']
                        check_in = row['check_in']
                        check_out = row['check_out']

                        check_out_time = check_out.hour + check_out.minute / 60 + check_out.second / 3600
                        check_in_time = check_in.hour + check_in.minute / 60 + check_in.second / 3600

                        # TODO: GET VARIABLE TO CHECK HALF DAY OFF
                        check_in_date = check_in.date()
                        leave_afternoon = http.request.env['hr.leave'].sudo().search([
                            ('employee_id', '=', emp.id),
                            ('date_from', '<=',
                             datetime.datetime(year=check_in_date.year, month=check_in_date.month,
                                               day=check_in_date.day,
                                               hour=13, minute=0, second=0)),
                            # development
                            ('date_to', '>=',
                             datetime.datetime(year=check_in_date.year, month=check_in_date.month,
                                               day=check_in_date.day,
                                               hour=17, minute=0, second=0)),  # development
                            ('state', '=', 'validate')
                        ])

                        vals = {
                            'employee_id': emp.id,
                            'check_in': row['check_in'] - datetime.timedelta(hours=7),
                            'check_out': None if pd.isnull(row['check_out']) else row['check_out'] - datetime.timedelta(
                                hours=7),
                            'check_out_status': True,
                        }

                        for day in week_days:
                            if int(day.dayofweek) == check_in_day and day.day_period == 'morning':
                                if leave_afternoon and check_out_time < day.hour_to:
                                    vals['check_out_status'] = False

                                late_duration = check_in_time - day.hour_from
                                late_duration_sec = datetime.timedelta(hours=late_duration).seconds

                            elif int(day.dayofweek) == check_in_day and day.day_period == 'afternoon':
                                if not leave_afternoon and check_out_time < day.hour_to:
                                    vals['check_out_status'] = False

                        http.request.env['hr.attendance'].create(vals)

        except Exception as e:
            raise UserWarning(e)
