from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)
class HrEmployeeInherited(models.AbstractModel):
    _inherit = "hr.employee.base"

    zk_teco_id = fields.Integer(string='ZK Teco ID')
    solution_sparepart_id = fields.Integer(string='Solution Spare part ID')
    solution_compressor_id = fields.Integer(string='Solution Compressor ID')
    solution_unit_warehouse_id = fields.Integer(string='Solution Unit Warehouse ID')