from odoo import api, fields, models, sql_db, _
import datetime
import logging
from collections import namedtuple
import math
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


class HrAttendanceGenerateTimeOff(models.Model):
    _inherit = 'hr.leave'

    subtract_diligence = fields.Boolean(string="Potong Kerajinan")

    def action_validate(self):
        for req in self:
            req.update({
                'payslip_status': True
            })
            return super(HrAttendanceGenerateTimeOff, req).action_validate()

    # @api.constrains('number_of_days')
    # def check_number_of_days(self):
    #     for req in self:
    #         calendar = req.employee_id.contract_ids
    #         start_date = req.date_from
    #         end_date = req.date_to
    #         duration = end_date - start_date
    #         if duration != req.number_of_days:
    #             raise ValidationError("Jumlah hari tidak sesuai")