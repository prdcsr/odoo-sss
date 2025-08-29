from odoo import models, fields
import logging
import pandas as pd
import numpy as np
import datetime
from io import BytesIO
import base64
import os

_logger = logging.getLogger(__name__)


class HrAttendancenImport(models.TransientModel):
    _name = 'attendance.import.form.solution'
    attendance_file = fields.Binary('File')
    department_id = fields.Many2one('hr.department', string='Departemen', )

    def act_import(self):
        decoded = base64.b64decode(self.attendance_file)
        path = '/var/lib/odoo/.local/share/Odoo/filestore'  # production
        # path = ''  # development

        with open(path + 'attendance.xls', 'wb') as f:
            f.write(decoded)

        df = pd.read_excel(path + 'attendance.xls')  # production

        if 'Nama' in df.columns:
            df['name'] = df['Nama']
        else:
            df['name'] = df['Name']

        if 'Tanggal' in df.columns:
            df['date'] = df['Tanggal']
        else:
            df['date'] = df['Date']

        if "NIK" in df.columns:
            df['id'] = df['NIK']
        else:
            df['id'] = df['No.']
        # df['Tanggal'] = str(pd.to_datetime(df['Tanggal'], format='%m/%d/%Y').dt.date)
        if 'Scan Masuk' in df.columns:
            df['check_in'] = np.where(df['Scan Masuk'].isnull(), np.NaN, df['Tanggal'] + ' ' + df['Scan Masuk'])
        else:
            df['check_in'] = np.where(df['Clock In'].isnull(), np.NaN, df['date'] + ' ' + df['Clock In'])

        df['check_in'] = pd.to_datetime(df['check_in'], format='%d/%m/%Y %H:%M')

        if 'Scan Pulang' in df.columns:
            df['check_out'] = np.where(df['Scan Pulang'].isnull(), df['date'] + ' ' + df['Scan Masuk'],
                                       df['Tanggal'] + ' ' + df['Scan Pulang'])
        else:
            df['check_out'] = np.where(df['Clock Out'].isnull(), df['date'] + ' ' + df['Clock In'],
                                       df['date'] + ' ' + df['Clock Out'])

        if "Departemen" in df.columns:
            df['Department'] = df['Departemen']

        df['check_out'] = pd.to_datetime(df['check_out'], format='%d/%m/%Y %H:%M')
        df.dropna(subset=['check_in'], inplace=True)

        for index, row in df.iterrows():
            employees = self.env['hr.employee'].search([
                ('zk_teco_id', '=', row['id']),
            ])
            # if row['Department'] == 'Sparepart':
            #     employees = self.env['hr.employee'].search([
            #         ('solution_sparepart_id', '=', row['id']),
            #         ('department_id', '=', department.id)
            #     ])
            # elif row['Department'] == 'Compressor':
            #     employees = self.env['hr.employee'].search([
            #         ('solution_compressor_id', '=', row['id']),
            #         ('department_id', '=', department.id)
            #     ])
            # elif row['Department'] == 'Unit':
            #     employees = self.env['hr.employee'].search([
            #         ('zk_teco_id', '=', row['id']),
            #         ('department_id', '=', department.id)
            #     ])

            for emp in employees:
                # if emp.department_id.name == row['Department']:
                calendar = emp.resource_calendar_id
                week_days = calendar.attendance_ids
                check_in_day = row['date']
                check_in = row['check_in']
                check_out = row['check_out']

                check_out_time = check_out.hour + check_out.minute / 60 + check_out.second / 3600
                check_in_time = check_in.hour + check_in.minute / 60 + check_in.second / 3600

                date_check = datetime.date(year=check_in.year, month=check_in.month, day=check_in.day)
                # out_check = datetime.datetime(year=check_in.year, month=check_in.month, day=check_in.day)
                attendance_check = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', emp.id),
                    ('attendance_date', '=', date_check),
                ])

                # TODO: GET VARIABLE TO CHECK HALF DAY OFF
                check_in_date = check_in.date()
                leave_afternoon = self.env['hr.leave'].sudo().search([
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
