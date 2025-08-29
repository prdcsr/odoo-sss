from collections import defaultdict
from datetime import datetime
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall, split as regex_split

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

class Repair(models.Model):
    _inherit = 'repair.order'

    operations = fields.One2many(
        'repair.line', 'repair_id', 'Parts',
        copy=True, readonly=True, states={'draft': [('readonly', False)], 'under_repair': [('readonly', False)]})
    
    fees_lines = fields.One2many(
        'repair.fee', 'repair_id', 'Operations',
        copy=True, readonly=True, states={'draft': [('readonly', False)], 'under_repair': [('readonly', False)]})
    
    cust_name =  fields.Text('customer Name',readonly=True, states={'draft': [('readonly', False)]})
    is_garansi = fields.Boolean('Ada Kartu Garansi',readonly=True,states={'draft': [('readonly', False)]})
    is_complete = fields.Boolean('Kartu garansi diisi dengan lengkap dan ada stamp Toko/Deale',readonly=True, states={'draft': [('readonly', False)]})
    is_damage_delivery = fields.Boolean('Tidak terjadi kerusakan karena kelalaian pemakaian, kesalahan penyimpanan atau kesalahan pengangkutan' 
    ,readonly=True,states={'draft': [('readonly', False)]})
    is_damage_self = fields.Boolean('Sistem unit tidak dirubah atau direparasi pihak ketiga',readonly=True,states={'draft': [('readonly', False)]})
    is_damage_nature = fields.Boolean('Kerusakan tidak disebabkan oleh bencana alam',readonly=True,states={'draft': [('readonly', False)]})
    is_consumables = fields.Boolean('Komponen kategori barang habis pakai',readonly=True,states={'draft': [('readonly', False)]})
    is_delivery_cost = fields.Boolean('Biaya pengembalian produk dari service center ditanggung oleh Dealer/Customer',readonly=True,states={'draft': [('readonly', False)]})
    origin_id = fields.Many2one(comodel_name='rma', string='Source Document')
    spbr_no = fields.Char(string='SPBR No')
    
    
    
    
class StockMove(models.Model):
    _inherit = "stock.move"

    invoice_method = fields.Selection([
        ('none', 'No Invoice'),
        ('b4repair', 'Before Repair'),
        ('after_repair', 'After Repair'),],string='Invoice Method', copy=False, default='none')

class InventoryAdjustmentLine(models.Model):
	_inherit = "stock.inventory.line"

	remark = fields.Text(string='Remark')
    