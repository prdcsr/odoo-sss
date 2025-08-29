# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class FnbHolidaySchedule(models.Model):
    _name = "fnb.holiday.schedule"
    _description = "FNB Holiday Schedule (Data Only)"
    _order = "date_start asc, name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    is_yearly = fields.Boolean(string="Repeat Every Year")
    is_national = fields.Boolean(string="National Holiday")
    notes = fields.Text()

    @api.constrains("date_start", "date_end")
    def _check_date_range(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError(_("End date cannot be earlier than start date."))

    @api.constrains("active", "date_start", "date_end")
    def _check_overlap(self):
        for rec in self:
            if not rec.active:
                continue
            candidates = self.search([('id', '!=', rec.id), ('active', '=', True)])
            for other in candidates:
                if rec.is_yearly or other.is_yearly:
                    if self._annually_overlap(rec, other):
                        raise ValidationError(_("Holiday '%s' overlaps with '%s' (annual).") % (rec.name, other.name))
                else:
                    if not (rec.date_end < other.date_start or other.date_end < rec.date_start):
                        raise ValidationError(_("Holiday '%s' overlaps with '%s'.") % (rec.name, other.name))

    @staticmethod
    def _annually_overlap(a, b):
        a_md = (a.date_start.month, a.date_start.day, a.date_end.month, a.date_end.day)
        b_md = (b.date_start.month, b.date_start.day, b.date_end.month, b.date_end.day)
        if a_md == b_md:
            return True
        return ((a.date_start.month, a.date_start.day) == (b.date_start.month, b.date_start.day) or
                (a.date_end.month, a.date_end.day) == (b.date_end.month, b.date_end.day))

    @api.model
    def is_holiday(self, dt):
        if isinstance(dt, str):
            try:
                dt = fields.Datetime.from_string(dt)
            except Exception:
                dt = fields.Datetime.now()
        the_date = dt.date() if hasattr(dt, 'date') else dt
        domain = [
            ('active', '=', True),
            ('is_yearly', '=', False),
            ('date_start', '<=', the_date),
            ('date_end', '>=', the_date),
        ]
        if self.search_count(domain):
            return True
        md = (the_date.month, the_date.day)
        yearly = self.search([('active', '=', True), ('is_yearly', '=', True)])
        for h in yearly:
            if ((h.date_start.month, h.date_start.day) <= md <= (h.date_end.month, h.date_end.day)):
                return True
        return False
