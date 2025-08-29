import datetime

from odoo import models, api, fields
import math


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime')

    # @api.multi
    def compute_sheet(self):

        super(PayslipOverTime, self).compute_sheet()
        for payslip in self:
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            if contract_ids:
                overtime_id = self.env['hr.overtime'].search(
                    [('employee_id', '=',
                      payslip.employee_id.id if payslip.employee_id.id else contract_ids[0].employee_id.id),
                     ('contract_id', '=', payslip.contract_id.id if payslip.contract_id.id else contract_ids[0].id),
                     ('state', '=', 'approved'), ('payslip_paid', '=', False)])

                weekly_list = []
                monthly_list = []
                for dat in overtime_id:
                    if 'LEMBUR JAM' not in dat.overtime_type_id.name or 'Cash Hour' not in dat.overtime_type_id.name:
                        monthly_list.append(dat.id)
                        payslip.overtime_ids = monthly_list
                    else:
                        weekly_list.append(dat.id)
                        payslip.overtime_ids = weekly_list

    @api.model
    def get_inputs(self, contracts, date_from, date_to, is_monthly=False):
        """
        function used for writing overtime record in payslip
        input tree.

        """
        res = super(PayslipOverTime, self).get_inputs(contracts, date_to, date_from)
        overtime_day = self.env.ref('ohrms_overtime.hr_salary_rule_overtime')
        overtime_hour = self.env.ref('ohrms_overtime.hr_salary_rule_overtime_hour')
        outside_type = self.env.ref('ohrms_overtime.hr_salary_rule_outside_daily')
        overtime_outside = self.env.ref('ohrms_overtime.hr_salary_rule_overtime_outside')

        # contract = self.contract_id
        # overtime_id = self.env['hr.overtime'].search([('employee_id', '=', self.employee_id.id),
        #                                               ('contract_id', '=', self.contract_id.id),
        #                                               ('state', '=', 'approved'), ('payslip_paid', '=', False)])
        contract = self.contract_id if self.contract_id.id else contracts
        overtime_id = self.env['hr.overtime'].search(
            [('employee_id', '=', self.employee_id.id if self.employee_id.id else contract.employee_id.id),
             ('contract_id', '=', self.contract_id.id if self.contract_id.id else contract.id),
             ('state', '=', 'approved'), ('payslip_paid', '=', False),
             ('date_from', '>=', date_from), ('date_to', '<=', date_to)
             ])
        hrs_amount = overtime_id.mapped('cash_hrs_amount')
        day_amount = overtime_id.mapped('cash_day_amount')
        cash_amount = sum(hrs_amount) + sum(day_amount)
        if overtime_id:
            # datetime_from = datetime.datetime.combine(date_from, datetime.datetime.min.time())
            for overtime in overtime_id:
                if not is_monthly:
                    start = datetime.datetime.strftime(overtime.date_from, '%d %H:%M')
                    end = datetime.datetime.strftime(overtime.date_to, '%d %H:%M')
                    amount = overtime.cash_day_amount
                    if 'LEMBUR LUAR KOTA' in overtime.overtime_type_id.name or 'DINAS LUAR KOTA TIDAK MENGINAP' in overtime.overtime_type_id.name or 'LEMBUR LUAR KOTA SUPIR DAN KENEK' in overtime.overtime_type_id.name:
                        amount = overtime.cash_day_amount
                    input_data = {
                        'name': overtime.overtime_type_id.name + ' ' + str(start) + ' - ' + str(end),
                        'code': overtime_day.code,
                        'amount': amount,
                        'contract_id': contract.id,
                        'number_of_hours': math.ceil(
                            overtime.days_no_tmp) if overtime.duration_type == 'hours' else None,
                        'number_of_days': math.ceil(overtime.days_no_tmp) if overtime.duration_type == 'days' else None
                    }

                    # if 'LEMBUR JAM' in overtime.overtime_type_id.name:
                    #     input_data['code'] = overtime_hour.code
                    #     input_data['amount'] = hrs_amount

                    overtime_list = [
                        'LEMBUR LUAR KOTA SUPIR DAN KENEK',
                        'DINAS LUAR KOTA TIDAK MENGINAP AREA 2',
                        'DINAS LUAR KOTA TIDAK MENGINAP AREA 1',
                    ]

                    if 'DINAS LUAR KOTA DAY' == overtime.overtime_type_id.name:
                        input_data['code'] = outside_type.code

                    if overtime.overtime_type_id.name in overtime_list :
                        input_data['code'] = overtime_outside.code
                    #
                    # if 'AREA 1' in overtime.overtime_type_id.name:
                    #     input_data['code'] = overtime_outside.code
                    #
                    # if 'AREA 2' in overtime.overtime_type_id.name:
                    #     input_data['code'] = overtime_outside.code

                    if 'LEMBUR JAM' not in overtime.overtime_type_id.name:
                        res.append(input_data)
                else:
                    start = datetime.datetime.strftime(overtime.date_from, '%d %H:%M')
                    end = datetime.datetime.strftime(overtime.date_to, '%d %H:%M')

                    input_data = {
                        'name': overtime.overtime_type_id.name + ' ' + str(start) + ' - ' + str(end),
                        'code': overtime_hour.code,
                        'amount': overtime.cash_hrs_amount,
                        'contract_id': contract.id,
                        'number_of_hours': math.ceil(
                            overtime.days_no_tmp) if overtime.duration_type == 'hours' else None,
                        'number_of_days': math.ceil(overtime.days_no_tmp) if overtime.duration_type == 'days' else None
                    }
                    if 'LEMBUR JAM' in overtime.overtime_type_id.name or 'Cash Hour' in overtime.overtime_type_id.name:
                        res.append(input_data)

        return res

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for recd in self.overtime_ids:
            if recd.type == 'cash':
                recd.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()
