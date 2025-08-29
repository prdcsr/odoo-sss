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

class PrintCashSummary(models.TransientModel):
    _name = "print.cash.summary"
    
    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date
    
    from_date = fields.Date(string='From Date', default=_get_from_date)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today)
    payment_summary_file = fields.Binary('Cash Summary Report')
    file_name = fields.Char('File Name')
    payment_report_printed = fields.Boolean('Cash Report Printed')
    cash_journal_ids = fields.Many2many('account.journal',
                                   string='Journals', required=True,)
    
    currency_id = fields.Many2one('res.currency','Currency', default=lambda self: self.env.user.company_id.currency_id)
    report_type = fields.Selection([('nota','Nota'),('statement','Statement')], default='statement', string='Generate Report Based on')
    
    
    # @api.multi
    def action_print_cash_summary(self,):
        ctx = dict(self.env.context) or {}
        workbook = xlwt.Workbook()
        column_heading_style = easyxf('font:height 200;font:bold True;')
        worksheet = workbook.add_sheet('Cash Summary')
        
        worksheet.write(1, 0, _('Date'), column_heading_style) 
        worksheet.write(1, 1, _('Statement Date'), column_heading_style)
        worksheet.write(1, 2, _('account'), column_heading_style)
        worksheet.write(1, 3, _('Partner'), column_heading_style)
        worksheet.write(1, 4, _('Journal'), column_heading_style)        
        worksheet.write(1, 5, _('Debit'), column_heading_style)
        worksheet.write(1, 6, _('Credit'), column_heading_style)
        worksheet.write(1, 7, _('Balance'), column_heading_style)        
        worksheet.write(1, 8, _('Analytic'), column_heading_style)
        worksheet.write(1, 9, _('Ref'), column_heading_style)

        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5000
        worksheet.col(7).width = 5000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 5000

        worksheet2 = workbook.add_sheet('Account Summary')
        worksheet2.write(3, 0, _('Account'), column_heading_style)
        worksheet2.write(3, 1, _('Debit'), column_heading_style)
        worksheet2.write(3, 2, _('Credit'), column_heading_style)
        worksheet2.write(3, 3, _('Balance'), column_heading_style)
        worksheet2.col(0).width = 5000
        worksheet2.col(1).width = 5000
        worksheet2.col(2).width = 5000
        worksheet2.col(3).width = 5000

        row = 2
        acc_row = 4
        [data] = self.read()
        for wizard in self:

            heading =  'Cash Report (' + str(wizard.currency_id.name) + ')'
            worksheet.write_merge(0, 0, 0, 5, heading, easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))
            worksheet2.write_merge(0, 0, 0, 5, heading, easyxf('font:height 200; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))
            if wizard.report_type == 'nota':                
                c_domain = [('parent_state','=','posted'),('date','>=',wizard.from_date),
                            ('date','<=',wizard.to_date),]
                i_domain = [('parent_state','=','posted'),('date','<',wizard.from_date),]
            else:
                c_domain = [('parent_state','=','posted'),('statement_id.date','>=',wizard.from_date),
                            ('statement_id.date','<=',wizard.to_date),]
                i_domain = [('parent_state','=','posted'),('statement_id.date','<',wizard.from_date),]
                    
            c_journal_id =[]      
            c_journal_id = wizard.cash_journal_ids.ids
            journal_ids = self.env['account.journal'].browse(data.get('cash_journal_ids'))
            #i_acc_name = journal_ids.default_debit_account_id.ids
            #for journal in journal_ids:
            #    i_acc_name += journal.default_debit_account_id.name

            c_domain += [('journal_id','in',c_journal_id)]
            i_domain += [('account_id', 'in',journal_ids.default_debit_account_id.ids)]

            invoice_objs = self.env['account.move.line'].search(c_domain)
                
                #[('statement_id.date','>=',wizard.from_date),
                #                                               ('statement_id.date','<=',wizard.to_date),
                #                                               ('journal_id', 'in', 
                #                                               ['Kas Besar Unit','Kas Kecil Unit']),
                #                                               ])

            summary_objs = self.env['account.move.line'].read_group(domain=c_domain,
                                                               fields=["account_id","debit","credit",
                                                                "balance","amount_currency",],
                                                                groupby=["account_id"],
                                                                #order=["balance"],
                                                                lazy=False,
                                                               )

            journal_obj = self.env['account.move.line'].search(i_domain)
            #journal_obj = self.env['account.move.line'].search([('statement_id.date','<=',wizard.from_date),                                                               
            #                                                   ('account_id.name', 'in', 
            #                                                   ['Kas Besar Unit','Kas Kecil Unit']),
            #                                                   ])
                                                               
            #ctx
            initial_debit = 0
            initial_credit = 0
            initial_balance = 0
            for account in journal_obj:
                initial_debit += account.debit
                initial_credit += account.credit
                initial_balance += account.balance
            
            
            

            worksheet.write(row, 0, wizard.from_date.strftime('%d-%m-%Y'))
            worksheet.write(row, 1, "")
            worksheet.write(row, 2, "00000000 Initial Balance")
            worksheet.write(row, 3, "")
            worksheet.write(row, 4, "")
            worksheet.write(row, 5, initial_debit)
            worksheet.write(row, 6, initial_credit)
            worksheet.write(row, 7, initial_balance)
            worksheet.write(row, 8, "")
            worksheet.write(row, 9, "")             
            row += 1
          

            worksheet2.write(1, 0, "From :")
            worksheet2.write(1, 1, wizard.from_date.strftime('%d-%m-%Y'))
            worksheet2.write(1, 2, "To :")
            worksheet2.write(1, 3, wizard.to_date.strftime('%d-%m-%Y'))                        
            

            worksheet2.write(acc_row, 0, "00000000 Initial Balance")
            #worksheet2.write(acc_row, 1, initial_debit)
            #worksheet2.write(acc_row, 2, initial_credit)
            worksheet2.write(acc_row, 3, initial_balance)                        
            acc_row += 1
            t_receive = initial_balance
            t_cost = 0
            t_bal = 0
            is_cost = False

            newlist = sorted(summary_objs, key=itemgetter('account_id'))


            #for res in summary_objs.sort(key=operator.itemgetter('account_id')):
            for res in newlist:    
                is_cash = False
                acc_name = res["account_id"][1]
                acc_name = acc_name._value
                for acc_id in journal_ids.default_debit_account_id.ids :
                    #raise Warning(_('journal : ') + acc_name + ' '+ str(res['account_id'][0]) + ' '+str(acc_id))
                    if acc_id == res['account_id'][0]:                        
                        is_cash = True
                if is_cash:
                    continue

                if not is_cost:
                    t_receive += abs(res["balance"])
                else:
                     t_cost += abs(res["balance"])

                if res['account_id'][0] == 1 :
                        worksheet2.write(acc_row, 0, 'Dari Bank')
                        #worksheet2.write(acc_row, 1, res["debit"])
                        #worksheet2.write(acc_row, 2, res["credit"])
                        worksheet2.write(acc_row, 3, abs(res["balance"]))
                        acc_row += 1    
                        
                        worksheet2.write(acc_row, 0, ' Total Receive')
                        #worksheet2.write(acc_row, 1, res["debit"])
                        #worksheet2.write(acc_row, 2, res["credit"])
                        worksheet2.write(acc_row, 3, t_receive)
                        acc_row += 2
                        is_cost = True
                        continue

                worksheet2.write(acc_row, 0, acc_name)
                #worksheet2.write(acc_row, 1, res["debit"])
                #worksheet2.write(acc_row, 2, res["credit"])
                worksheet2.write(acc_row, 3, abs(res["balance"]))
                acc_row += 1
                
                
            
            worksheet2.write(acc_row, 0, ' Total Out')
            #worksheet2.write(acc_row, 1, res["debit"])
            #worksheet2.write(acc_row, 2, res["credit"])
            worksheet2.write(acc_row, 3, t_cost)
            acc_row +=1
            t_bal = t_receive - t_cost 
            
            worksheet2.write(acc_row, 0, ' Balance')
            #worksheet2.write(acc_row, 1, res["debit"])
            #worksheet2.write(acc_row, 2, res["credit"])
            worksheet2.write(acc_row, 3, t_bal)

            for invoice in invoice_objs:

                new_invoice_date = invoice.date.strftime('%d-%m-%Y')
                statement_date = ''
                #if type(invoice.statement_id.date) is datetime :
                statement_date = invoice.statement_id.date.strftime('%d-%m-%Y')

                worksheet.write(row, 0, new_invoice_date)
                worksheet.write(row, 1, statement_date)
                worksheet.write(row, 2, invoice.account_id.display_name)
                worksheet.write(row, 3, invoice.partner_id.name)
                worksheet.write(row, 4, invoice.journal_id.name)
                worksheet.write(row, 5, invoice.debit)
                worksheet.write(row, 6, invoice.credit)
                worksheet.write(row, 7, invoice.balance)
                worksheet.write(row, 8, invoice.analytic_account_id.name)
                worksheet.write(row, 9, invoice.name)             
                row += 1

            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.payment_summary_file = excel_file
            wizard.file_name = 'Cash Summary Report.xls'
            wizard.payment_report_printed = True
            fp.close()
            return {
                    'view_mode': 'form',
                    'res_id': wizard.id,
                    'res_model': 'print.cash.summary',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                       }
