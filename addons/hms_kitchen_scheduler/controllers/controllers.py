# -*- coding: utf-8 -*-
# from odoo import http


# class HmsKitchenScheduler(http.Controller):
#     @http.route('/hms_kitchen_scheduler/hms_kitchen_scheduler/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hms_kitchen_scheduler/hms_kitchen_scheduler/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hms_kitchen_scheduler.listing', {
#             'root': '/hms_kitchen_scheduler/hms_kitchen_scheduler',
#             'objects': http.request.env['hms_kitchen_scheduler.hms_kitchen_scheduler'].search([]),
#         })

#     @http.route('/hms_kitchen_scheduler/hms_kitchen_scheduler/objects/<model("hms_kitchen_scheduler.hms_kitchen_scheduler"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hms_kitchen_scheduler.object', {
#             'object': obj
#         })
