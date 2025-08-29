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

    # @api.model
    # @http.route('/hr_attendance/import', auth='user', type='http', website=False, csrf=False)
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
                # if not employee.ids:
                #     emp = {
                #         'name': row['name'],
                #         'active': True,
                #         'zk_teco_id': row['personnel_id'],
                #     }
                #     employee = http.request.env['hr.employee'].create(emp)

                # if not employee.zk_teco_id:
                #     employee.write({
                #         'zk_teco_id': row['personnel_id']
                #     })

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

                # leave_morning = request.env['hr.leave'].sudo().search([
                #     ('employee_id', '=', employee.id),
                #     ('date_from', '<=',
                #      datetime.datetime(year=check_in_date.year, month=check_in_date.month, day=check_in_date.day,
                #                        hour=8, minute=0, second=0)),
                #     ('date_to', '>=',
                #      datetime.datetime(year=check_in_date.year, month=check_in_date.month, day=check_in_date.day,
                #                        hour=12, minute=0, second=0)),
                #     ('state', '=', 'validate')
                # ])

                for day in week_days:
                    if int(day.dayofweek) == check_in_day and day.day_period == 'morning':
                        if leave_afternoon and check_out_time < day.hour_to:
                            vals['check_out_status'] = False

                        late_duration = check_in_time - day.hour_from
                        late_duration_sec = datetime.timedelta(hours=late_duration).seconds

                        # if not leave_morning and day.hour_to > check_in_time >= day.hour_from and late_duration_sec > 300:
                        #     off_types = request.env['hr.leave.type'].sudo().search([
                        #         ('code', '=', 'telat2023'),
                        #     ])
                        #     start_time = datetime.time(8, 0, 0)
                        #     end_time = datetime.time(17, 0, 0)
                        #     check_time = str(datetime.timedelta(hours=check_in_time)).rsplit(':', 1)[0]
                        #     late_data = {
                        #         'employee_id': employee.id,
                        #         'date_from': datetime.datetime.combine(check_in_date, start_time),
                        #         'request_date_from': datetime.datetime.combine(check_in_date, start_time),
                        #         'date_to': datetime.datetime.combine(check_out.date(), end_time),
                        #         'request_date_to': datetime.datetime.combine(check_out.date(), end_time),
                        #         'name': 'Terlambat tanggal {check_in}, waktu check in: {check_in_time}'.format(
                        #             check_in=check_in_date, check_in_time=check_time),
                        #         # 'request_unit_half': True,
                        #         'payslip_status': True,
                        #         # 'request_date_from_period': 'am',
                        #         'number_of_days': 1,
                        #     }
                        #     for off_type in off_types:
                        #         if off_type.validity_start <= check_in and off_type.validity_stop >= check_out:
                        #             late_data['holiday_status_id'] = off_type.id
                        #
                        #     request.env['hr.leave'].create(late_data)

                    elif int(day.dayofweek) == check_in_day and day.day_period == 'afternoon':
                        if not leave_afternoon and check_out_time < day.hour_to:
                            vals['check_out_status'] = False

                attend = http.request.env['hr.attendance'].create(vals)

                # TODO: CREATE TIME OFF
                # if attend.worked_hours <= 1:
                #     off_types = request.env['hr.leave.type'].sudo().search([
                #         ('code', '=', 'lupaabsen2023'),
                #     ])
                #     start_time = datetime.time(13, 0, 0)
                #     end_time = datetime.time(17, 0, 0)
                #     vals = {
                #         'employee_id': employee.id,
                #         'date_from': datetime.datetime.combine(check_in_date, start_time),
                #         'request_date_from': datetime.datetime.combine(check_in_date, start_time),
                #         'request_date_to': datetime.datetime.combine(check_out.date(), end_time),
                #         'date_to': datetime.datetime.combine(check_out.date(), end_time),
                #         'name': 'Lupa absen pulang tanggal {check_out}'.format(check_out=check_in_date),
                #         'payslip_status': True,
                #         # 'request_unit_half': True,
                #         # 'request_date_from_period': 'pm',
                #         'number_of_days': 1,
                #     }
                #     for off_type in off_types:
                #         if off_type.validity_start <= check_in and off_type.validity_stop >= check_out:
                #             vals['holiday_status_id'] = off_type.id
                #     _logger.info('EMPLOYEE ID: {}'.format(employee.id))
                #
                #     request.env['hr.leave'].create(vals)

            os.remove(path + 'attendance.xls')  # production
            # os.remove('attendance.xls')
            return 'Success'
        except Exception as e:
            raise UserWarning(e)
