# -*- coding: utf-8 -*-
from odoo import http

# class Optecha(http.Controller):
#     @http.route('/optecha/optecha/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/optecha/optecha/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('optecha.listing', {
#             'root': '/optecha/optecha',
#             'objects': http.request.env['optecha.optecha'].search([]),
#         })

#     @http.route('/optecha/optecha/objects/<model("optecha.optecha"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('optecha.object', {
#             'object': obj
#         })