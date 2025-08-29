# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 BroadTech IT Solutions Pvt Ltd 
#    (<http://broadtech-innovations.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools.misc import xlwt
import io
import base64
from xlwt import easyxf
import datetime
#import operator
from operator  import itemgetter
from odoo.exceptions import UserError,Warning

class PrintPicingList(models.TransientModel):
    _name = "print.picking.list"
    
    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date
    
    from_date = fields.Date(string='From Date', default=fields.Date.context_today)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today)
    picking_list_file = fields.Binary('Picking List Report')
    file_name = fields.Char('File Name')
    picking_report_printed = fields.Boolean('Picking Report Printed')
    picking_type_ids = fields.Many2many('stock.picking.type', string='Picking Type', )
    
    #currency_id = fields.Many2one('res.currency','Currency', default=lambda self: self.env.user.company_id.currency_id)
    report_type = fields.Selection([('done','Terkirim'),('notdone','Belum Terkirim'),('all','Semua')], default='notdone', string='Report Transfer')
    
    
    # @api.multi
    def action_print_picking_list(self,):
        ctx = dict(self.env.context) or {}
        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_sheet('Picking List')
        
        worksheet.write(4, 0, _('Date'), column_heading_style) 
        worksheet.write(4, 1, _('Schedule Date'), column_heading_style)
        worksheet.write(4, 2, _('No. Transfer'), column_heading_style)
        worksheet.write(4, 3, _('No. Surat Jalan'), column_heading_style)
        worksheet.write(4, 4, _('Partner'), column_heading_style)
        worksheet.write(4, 5, _('Kota'), column_heading_style)
        worksheet.write(4, 6, _('Ekspedisi'), column_heading_style)
        worksheet.write(4, 7, _('Product'), column_heading_style)
        worksheet.write(4, 8, _('Name'), column_heading_style)
        worksheet.write(4, 9, _('Qty'), column_heading_style)
        worksheet.write(4, 10, _('Status'), column_heading_style)

        worksheet.col(0).width = 4000
        worksheet.col(1).width = 4000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 4000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 2000
        worksheet.col(10).width = 5000


        row = 5
        #acc_row = 4
        [data] = self.read()
        for wizard in self:

            if wizard.report_type == 'done':
                c_domain = [('state','=','done'),('date_done','>=',wizard.from_date),
                            ('date_done','<=',wizard.to_date),('picking_type_id','in',wizard.picking_type_ids.ids),]
                i_text = 'Terkirim'
            elif wizard.report_type == 'notdone':
                c_domain = [('state','!=','done'),('scheduled_date','>=',wizard.from_date),
                            ('scheduled_date','<=',wizard.to_date),('picking_type_id','in',wizard.picking_type_ids.ids),]
                i_text = 'Belum Terkirim'
                #i_domain = [('parent_state','=','posted'),('statement_id.date','<',wizard.from_date),]
            else:
                c_domain = [('state','in',('done', 'waiting', 'assigned', 'confirmed')),('scheduled_date','>=',wizard.from_date),
                            ('scheduled_date','<=',wizard.to_date),('picking_type_id','in',wizard.picking_type_ids.ids),]
                i_text = 'Semua'
            #heading =  'Picking List (' + str(wizard.picking_type_ids.name) + ') ' + i_text
            heading =  'Picking List Report' #(' + str(wizard.picking_type_ids.name) + ') ' + i_text
            worksheet.write_merge(0, 0, 0, 8, heading, easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))        
            #c_account_id =[]      
            
            picking_ids = self.env['stock.picking'].search(c_domain)
            worksheet.write(1, 0, "From :")
            worksheet.write(1, 1, wizard.from_date.strftime('%d-%m-%Y'))
            worksheet.write(1, 2, "To :")
            worksheet.write(1, 3, wizard.to_date.strftime('%d-%m-%Y'))                        
            
            
            for picking in picking_ids.sorted(key=lambda m: m.scheduled_date):
          
                scheduled_date = picking.scheduled_date.strftime('%d-%m-%Y')
                date_done = scheduled_date
                if picking.date_done:
                    date_done = picking.date_done.strftime('%d-%m-%Y')
                #else:
                #   statement_date = ''
                

                worksheet.write(row, 0, date_done)
                worksheet.write(row, 1, scheduled_date)
                worksheet.write(row, 2, picking.display_name)
                worksheet.write(row, 3, picking.origin)
                worksheet.write(row, 4, picking.partner_id.name)
                # worksheet.write(row, 4, picking.partner_id.city)
                worksheet.write(row, 5, picking.partner_id.city )
                worksheet.write(row, 6, picking.carrier_id.name)
                worksheet.write(row, 7, '')
                worksheet.write(row, 8, '')
                worksheet.write(row, 10, picking.state)         
                row += 1
                stock_move_ids = self.env['stock.move'].search([('id','in',picking.move_lines.ids)])
                for move in stock_move_ids:
                    #worksheet.write(row,0,'')
                    #worksheet.write(row,1,'')
                    #worksheet.write(row,2,''')
                    #worksheet.write(row,3,''')
                    #worksheet.write(row,4,''')
                    worksheet.write(row,7,move.product_id.default_code)
                    worksheet.write(row,8,move.product_id.name)
                    if wizard.report_type == 'done':
                        worksheet.write(row,9,move.quantity_done)
                    else:
                        worksheet.write(row,9,move.product_uom_qty)
                    row += 1



            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.picking_list_file = excel_file
            wizard.file_name = 'Picking List Report.xls'
            wizard.picking_report_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'print.picking.list',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                       }
