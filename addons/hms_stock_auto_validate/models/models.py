# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class hms_stock_auto_validate(models.Model):
#     _name = 'hms_stock_auto_validate.hms_stock_auto_validate'
#     _description = 'hms_stock_auto_validate.hms_stock_auto_validate'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
