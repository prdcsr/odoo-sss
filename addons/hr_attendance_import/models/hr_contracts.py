from odoo import api, models, fields
import logging
import datetime
import pandas as pd

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.contract'

    outside_meal_allowance = fields.Monetary(string='Uang Makan Luar Kota')