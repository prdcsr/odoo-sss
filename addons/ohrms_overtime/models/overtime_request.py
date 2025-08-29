# -*- coding: utf-8 -*-

import math

import pandas as pd
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('days_no_tmp')
    def _onchange_days_no_tmp(self):
        self.days_no = self.days_no_tmp

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  states={'draft': [('readonly', False)]},
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    overtime_officer_id = fields.Many2one('res.users', string="Overtime Officer",
                                          related="employee_id.leave_manager_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User",
                                   related='employee_id.user_id',
                                   default=lambda self: self.env.uid,
                                   store=True)
    current_user_boolean = fields.Boolean()
    project_id = fields.Many2one('project.project', string="Project")
    project_manager_id = fields.Many2one('res.users', string="Project Manager")
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id",
                                  )
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date to')
    days_no_tmp = fields.Float('Hours', compute="_get_days", store=True)
    days_no = fields.Float('No. of Days', store=True)
    desc = fields.Text('Description')

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('f_approve', 'Waiting'),
        ('refused', 'Refused'),
        ('approved1', 'Second Approval'),
        ('approved', 'Approved')], string='Status', readonly=True, tracking=True, copy=False, default='draft')

    # state = fields.Selection([('draft', 'Draft'),
    #                           ('f_approve', 'Waiting'),
    #                           ('approved', 'Approved'),
    #                           ('refused', 'Refused')], string="state",
    #                          default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave ID")
    holiday_id = fields.Many2one('hr.leave',
                                 string="Holiday ID")
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash')], default="cash", required=True, string="Type")
    # type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="cash", required=True, string="Type")
    overtime_type_id = fields.Many2one('overtime.type', domain="[('type','=',type),('duration_type','=', "
                                                               "duration_type)]")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=False)
    first_approver_id = fields.Many2one(
        'hr.employee', string='First Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the time off')
    second_approver_id = fields.Many2one(
        'hr.employee', string='Second Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the time off with second level (If time off type need second validation)')
    rest_duration = fields.Float(String="Rest Duration")

    # validation_type = fields.Selection('Validation Type', related='overtime_type_id.validation_type', readonly=False)

    # @api.depends('current_user')
    # def check_current_user(self):
    # for i in self:
    # if self.env.user.id == self.employee_id.user_id.id:
    #     i.update({
    #         'current_user_boolean': True,
    #     })

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                    'overtime_officer_id': sheet.employee_id.leave_manager_id.id,
                    'rest_duration': sheet.contract_id.rest_duration or 0
                })

    @api.onchange('rest_duration')
    def _change_rest_duration(self):
        for req in self:
            if req.days_no_tmp > 0:
                req._get_days()
                if req.rest_duration >= 0 and req.rest_duration < req.days_no_tmp:
                    req.write({
                        'days_no_tmp': req.days_no_tmp - req.rest_duration if req.duration_type == 'hours' else req.days_no_tmp
                    })
                else:
                    raise UserError(_("Rest duration must be lower than overtime duration."))

    @api.depends('project_id')
    def _get_project_manager(self):
        for sheet in self:
            if sheet.project_id:
                sheet.update({
                    'project_manager_id': sheet.project_id.user_id.id,
                })

    @api.depends('date_from', 'date_to')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            if sheet.date_from and sheet.date_to:
                start_dt = fields.Datetime.from_string(sheet.date_from)
                finish_dt = fields.Datetime.from_string(sheet.date_to)
                finish_minutes = finish_dt.minute
                finish_hour = finish_dt.hour
                if finish_minutes >= 50:
                    finish_dt = finish_dt.replace(hour=finish_hour + 1, minute=0)
                s = finish_dt - start_dt
                difference = relativedelta.relativedelta(finish_dt, start_dt)
                hours = difference.hours
                minutes = difference.minutes
                days_in_mins = s.days * 24 * 60
                hours_in_mins = hours * 60
                days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))

                diff = finish_dt - start_dt
                days, seconds = diff.days, diff.seconds
                duration_float = days * 24 + seconds / 3600
                hours = math.ceil(days * 24 + seconds // 3600)

                if 0.83 <= duration_float < 1:
                    hours = 1
                else:
                    hours = math.ceil(days * 24 + seconds // 3600)

                if hours > 0:
                    if sheet.rest_duration >= 0 and sheet.rest_duration < hours:
                        hours = hours - sheet.rest_duration if sheet.duration_type == 'hours' else hours
                    else:
                        raise UserError(_("Rest duration must be lower than overtime duration."))

                # TODO: need flaging department to check if department overtime hour -1
                if (sheet.department_id.id in [4, 21, 22]) and hours > 1 and sheet.overtime_type_id.name != "LEMBUR JAM EKSPEDISI":
                    hours -= 1
                sheet.update({
                    'days_no_tmp': hours if sheet.duration_type == 'hours' else math.ceil(days_no),
                })

    @api.onchange('overtime_type_id', 'days_no_tmp')
    def _get_hour_amount(self):
        if self.overtime_type_id.rule_line_ids and self.duration_type == 'hours':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_hour:
                        cash_amount = self.contract_id.over_hour * self.days_no_tmp
                        self.cash_hrs_amount = cash_amount
                    else:
                        raise UserError(_("Hour Overtime Needs Hour Wage in Employee Contract."))
        elif self.overtime_type_id.rule_line_ids and self.duration_type == 'days':
            for recd in self.overtime_type_id.rule_line_ids:
                if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                    if self.contract_id.over_day and "LEMBUR HARIAN" in self.overtime_type_id.name:
                        cash_amount = self.contract_id.over_day * math.ceil(self.days_no_tmp)
                        self.cash_day_amount = cash_amount
                    elif self.contract_id.outside_meal_allowance and "DINAS LUAR KOTA DAY" == self.overtime_type_id.name:
                        cash_amount = self.contract_id.outside_meal_allowance * math.ceil(self.days_no_tmp)
                        self.cash_day_amount = cash_amount
                    elif self.contract_id.over_jabodetabek and "LEMBUR LUAR KOTA " in self.overtime_type_id.name:
                        cash_amount = self.contract_id.over_jabodetabek * math.ceil(self.days_no_tmp)
                        self.cash_day_amount = cash_amount
                    elif self.contract_id.outside_non_overnight and 'AREA 1' in self.overtime_type_id.name:
                        cash_amount = self.contract_id.outside_non_overnight * math.ceil(self.days_no_tmp)
                        self.cash_day_amount = cash_amount
                    elif self.contract_id.outside_non_overnight_far_area and 'AREA 2' in self.overtime_type_id.name:
                        cash_amount = self.contract_id.outside_non_overnight_far_area * math.ceil(self.days_no_tmp)
                        self.cash_day_amount = cash_amount
                    else:
                        raise UserError(_("Day Overtime Needs Day Wage in Employee Contract."))

    def submit_to_f(self):
        # notification to employee
        recipient_partners = [(4, self.current_user.partner_id.id)]
        body = "Your OverTime Request Waiting Finance Approve .."
        msg = _(body)
        # if self.current_user:
        #     self.message_post(body=msg, partner_ids=recipient_partners)

        # notification to finance :
        group = self.env.ref('account.group_account_invoice', False)
        recipient_partners = []
        # for recipient in group.users:
        #     recipient_partners.append((4, recipient.partner_id.id))

        body = "You Get New Time in Lieu Request From Employee : " + str(
            self.employee_id.name)
        msg = _(body)
        # self.message_post(body=msg, partner_ids=recipient_partners)
        return self.sudo().write({
            'state': 'f_approve',
            'overtime_officer_id': self.sudo().employee_id.leave_manager_id.id
        })

    # def approve(self):
    #     return self.sudo().write({
    #         'state': 'approved',
    #     })

    def reset_to_draft(self):
        for req in self:
            if req.state is not 'draft' or 'submit_to_f' or 'f_approve':
                req.write({
                    'state': 'draft',
                })
                if req.leave_id and req.leave_id.state == 'approved':
                    leave = req.leave_id
                    leave.action_refuse()
                    leave.action_draft()

    def approve(self):
        for req in self:
            current_employee = self.env.user.employee_id
            # is_all_approver = self.env.user.has_group('ohrms_overtime.group_hr_overtime_user')
            if req.state != 'f_approve':
                raise UserError('Status pengajuan lembur harus menununggu!')
            # if req.overtime_officer_id != current_employee.id:
            #     raise UserError('User {name} tidak dapat menerima pengajuan ini'.format(name=current_employee.name))
            if req.overtime_type_id.type == 'cash' and (
                    'DINAS LUAR KOTA DAY' == req.overtime_type_id.name or 'LEMBUR LUAR KOTA' in req.overtime_type_id.name):
                diff = req.date_to - req.date_from
                year = req.date_from.year % 2000
                off_types = req.env['hr.leave.type'].sudo().search([
                    ('code', '=', 'dinasluarkota_' + str(year)),
                ])
                if 'LEMBUR LUAR KOTA ' in req.overtime_type_id.name:
                    off_types = req.env['hr.leave.type'].sudo().search([
                        ('code', '=', 'dinasluarkotasupir_' + str(year)),
                    ])
                holiday_vals = {
                    'employee_id': req.employee_id.id,
                    'date_from': req.date_from,
                    'request_date_from': req.date_from,
                    'request_date_to': req.date_to,
                    'date_to': req.date_to,
                    'name': 'Dinas',
                    'payslip_status': True,
                    'number_of_days': diff.days,
                    # 'state': 'validate'
                }
                # TODO: BUTTON ACTION FOR VALIDATE ATTENDANCE OFF

                for off_type in off_types:
                    if off_type.validity_start <= req.date_from.date() and off_type.validity_stop >= req.date_to.date():
                        holiday_vals['holiday_status_id'] = off_type.id
                holiday = self.env['hr.leave'].sudo().create(
                    holiday_vals)

                holiday.action_approve()

                req.holiday_id = holiday.id

            req.write({
                'state': 'approved1',
                'first_approver_id': current_employee.id
            })

    def validate(self):
        for rec in self:

            current_employee = self.env.user.employee_id
            # is_all_approver = self.env.user.has_group('ohrms_overtime.group_hr_overtime_user')
            if rec.state != 'approved1':
                raise UserError('Pengajuan lembur wajib disetujui oleh pihak yang bertanggung jawab !')
            # if self.manager_id != current_employee.id :
            #     raise UserError('User {name} tidak dapat menerima pengajuan ini'.format(name=current_employee.name))
            # if self.overtime_type_id.type == 'leave':
            #     if self.duration_type == 'days':
            #         holiday_vals = {
            #             'name': 'Overtime',
            #             'holiday_status_id': self.overtime_type_id.leave_type.id,
            #             'number_of_days': self.days_no_tmp,
            #             'notes': self.desc,
            #             'holiday_type': 'employee',
            #             'employee_id': self.employee_id.id,
            #             'state': 'validate',
            #         }
            #     else:
            #         day_hour = self.days_no_tmp / HOURS_PER_DAY
            #         holiday_vals = {
            #             'name': 'Overtime',
            #             'holiday_status_id': self.overtime_type_id.leave_type.id,
            #             'number_of_days': day_hour,
            #             'notes': self.desc,
            #             'holiday_type': 'employee',
            #             'employee_id': self.employee_id.id,
            #             'state': 'validate',
            #         }
            #     holiday = self.env['hr.leave.allocation'].sudo().create(
            #         holiday_vals)
            #     self.leave_id = holiday.id
            # if rec.overtime_type_id.type == 'cash' and ('DINAS LUAR KOTA DAY' == rec.overtime_type_id.name or 'LEMBUR LUAR KOTA' in rec.overtime_type_id.name):
            if rec.overtime_type_id.type == 'cash' and rec.holiday_id:
                leave_instance = self.env['hr.leave'].sudo().search([
                    ('id', '=', rec.holiday_id.id)
                ])
                if leave_instance.state != 'validate' and leave_instance.state == 'validate1':
                    leave_instance.action_validate()

            # notification to employee :
            recipient_partners = [(4, rec.current_user.partner_id.id)]
            body = "Pengajuan Lembur anda tanggal " + str(rec.date_from) + ' ' + str(
                rec.date_to) + ' telah disetujui oleh ' + current_employee.name
            msg = _(body)

            # if 'DINAS' not in self.overtime_type_id.name:
            #     self.message_post(body=msg, partner_ids=recipient_partners)

            return self.sudo().write({
                'state': 'approved',
                'second_approver_id': current_employee.id
            })

            # return {
            #     'name': _('Leave Adjust'),
            #     'context': {'default_til_id': self.id},
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'leave.adjust',
            #     'view_id': self.env.ref('leave_management.leave_adjust_wizard_view',
            #                             False).id,
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'target': 'new',
            # }

    def reject(self):
        for rec in self:
            rec.state = 'refused'
            leave_instance = self.env['hr.leave'].sudo().search([
                ('id', '=', rec.holiday_id.id)
            ])
            leave_instance.action_refuse()

        # return {
        #     'name': _('Refuse Business Trip'),
        #     'context': {'default_overtime_id': self.id},
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'refuse.wzrd',
        #     'view_id': self.env.ref('leave_management.refuse_wzrd_view',
        #                             False).id,
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'target': 'new',
        # }

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_(
                    'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        overtime = super(HrOverTime, self.sudo()).create(values)
        overtime.submit_to_f()
        return overtime

    def unlink(self):
        for overtime in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete TIL request which is not in draft state.'))
        for overtime in self.filtered(
                lambda overtime: overtime.leave_id and overtime.leave_id.state != 'draft'):
            raise UserError(
                _('Terdapat pengajuan time off yang telah di setujui, silahkan hapus pengajuan terlebuh dahulu')
            )
        return super(HrOverTime, self).unlink()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.resource_calendar_id.global_leave_ids:
                leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                overtime_dates = pd.date_range(self.date_from, self.date_to).date
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date == over_time:
                            holiday = True
            if holiday:
                self.write({
                    'public_holiday': 'You have Public Holidays in your Overtime request.'})
            else:
                self.write({'public_holiday': ' '})
            hr_attendance = self.env['hr.attendance'].search(
                [('check_in', '>=', self.date_from),
                 ('check_in', '<=', self.date_to),
                 ('employee_id', '=', self.employee_id.id)])
            self.update({
                'attendance_ids': [(6, 0, hr_attendance.ids)]
            })


class HrOverTimeType(models.Model):
    _name = 'overtime.type'

    name = fields.Char('Name')
    type = fields.Selection([('cash', 'Cash'),
                             ('leave', 'Leave ')])

    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('overtime.type.rule', 'type_line_id')

    # validation_type = fields.Selection([
    #     ('no_validation', 'No Validation'),
    #     ('hr', 'Overtime Officer'),
    #     ('manager', 'Team Leader'),
    #     ('both', 'Team Leader and Overtime Officer')], default='hr', string='Validation')

    # responsible_id = fields.Many2one('res.users', 'Responsible',
    #                                  domain=lambda self: [
    #                                      ('groups_id', 'in', self.env.ref('ohrms_overtime.group_hr_overtime_user').id)],
    #                                  help="This user will be responsible for approving this type of times off"
    #                                       "This is only used when validation is 'hr' or 'both'", )

    @api.onchange('duration_type')
    def _get_leave_type(self):
        dur = ''
        ids = []
        if self.duration_type:
            if self.duration_type == 'days':
                dur = 'day'
            else:
                dur = 'hour'
            leave_type = self.env['hr.leave.type'].search([('request_unit', '=', dur)])
            for recd in leave_type:
                ids.append(recd.id)
            self.leave_compute = ids


class HrOverTimeTypeRule(models.Model):
    _name = 'overtime.type.rule'

    type_line_id = fields.Many2one('overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    hrs_amount = fields.Float('Rate', required=True)
