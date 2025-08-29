from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)
class HrAttendance(models.Model):
    _name = 'hr.attendance.import'

    def test(self):
        _logger.info('clicked')
