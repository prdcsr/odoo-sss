from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class HrSummaryExport(models.TransientModel):
    _name = 'summary.export.form'
