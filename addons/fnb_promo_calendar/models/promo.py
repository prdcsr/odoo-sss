# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

WEEKDAY_SELECTION = [
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
]

class FnbPromoSchedule(models.Model):
    _name = "fnb.promo.schedule"
    _description = "FNB Promotion Schedule (Data Only)"
    _order = "date_start asc, time_start asc, name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    weekday_ids = fields.Selection(WEEKDAY_SELECTION, string="Day of Week")
    weekday_multi = fields.Many2many("fnb.weekday", string="Days")

    time_start = fields.Float(string="Time From")
    time_end = fields.Float(string="Time To")

    notes = fields.Text()

    @api.constrains("date_start", "date_end")
    def _check_date_range(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError(_("End date cannot be earlier than start date."))

    @api.constrains("time_start", "time_end")
    def _check_time_window(self):
        for rec in self:
            if rec.time_start and rec.time_end and rec.time_end <= rec.time_start:
                raise ValidationError(_("Time To must be greater than Time From."))

    @api.constrains("active", "date_start", "date_end", "time_start", "time_end")
    def _check_overlap(self):
        for rec in self:
            if not rec.active:
                continue
            domain = [
                ('id', '!=', rec.id),
                ('active', '=', True),
                ('date_start', '<=', rec.date_end),
                ('date_end', '>=', rec.date_start),
            ]
            for other in self.search(domain):
                a1, a2 = (rec.time_start or 0.0, rec.time_end or 24.0)
                b1, b2 = (other.time_start or 0.0, other.time_end or 24.0)
                if (a1 < b2) and (b1 < a2):
                    if self._weekday_intersect(rec, other):
                        raise ValidationError(_("Overlap with '%s' in date/time window.") % other.name)

    @staticmethod
    def _weekday_intersect(a, b):
        if not a.weekday_ids and not a.weekday_multi and not b.weekday_ids and not b.weekday_multi:
            return True
        def codes(rec):
            s = set()
            if rec.weekday_ids:
                s.add(rec.weekday_ids)
            if rec.weekday_multi:
                s |= set(rec.weekday_multi.mapped('code'))
            return s
        ac, bc = codes(a), codes(b)
        if not ac:
            ac = set([str(i) for i in range(7)])
        if not bc:
            bc = set([str(i) for i in range(7)])
        return bool(ac & bc)

    @api.model
    def get_active_promotions(self, dt):
        if isinstance(dt, str):
            try:
                dt = fields.Datetime.from_string(dt)
            except Exception:
                dt = fields.Datetime.now()
        date_only = dt.date()
        weekday = str(dt.weekday())
        hour_decimal = dt.hour + dt.minute/60.0
        domain = [
            ('active', '=', True),
            ('date_start', '<=', date_only),
            ('date_end', '>=', date_only),
        ]
        promos = self.search(domain)
        def match_weekday(rec):
            if not rec.weekday_ids and not rec.weekday_multi:
                return True
            if rec.weekday_ids and rec.weekday_ids == weekday:
                return True
            if rec.weekday_multi and any(wd.code == weekday for wd in rec.weekday_multi):
                return True
            return False
        def match_time(rec):
            start = rec.time_start if rec.time_start else 0.0
            end = rec.time_end if rec.time_end else 24.0
            return start <= hour_decimal <= end
        return promos.filtered(lambda r: match_weekday(r) and match_time(r)).ids

class FnbWeekday(models.Model):
    _name = "fnb.weekday"
    _description = "FNB Weekday"

    name = fields.Char(required=True)
    code = fields.Selection(WEEKDAY_SELECTION, required=True)

    _sql_constraints = [
        ('weekday_code_unique', 'unique(code)', 'Weekday code must be unique.')
    ]
