# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RmaForm(models.Model):
    _name = 'optecha.rma'

    name = fields.Char(string="Name")
    opportunity_id = fields.Many2one('crm.lead',string="Opportunity Name")
    orders = fields.Many2one('sale.order',string="Order", domain="[('opportunity_id','=',opportunity_id)]")
    order_lines = fields.Many2one('sale.order.line', string="Order Line",
                                  domain="[('order_id','=',orders)]")
    reason = fields.Char(string="Reasons")
    partner_id = fields.Many2one('res.partner',string="Customer")
    product_id = fields.Many2one('product.product', string="Product",store=True)
    state = fields.Selection([
        ('add_product', 'Require Additional Product'),
        ('fixtures', 'Fixture Failuire'),
        ('contact_manufacturer', 'Conatact Manufacturer'),
        ('done', 'Done')
    ])

    @api.onchange('order_lines')
    def _onchange_order_lines(self):
        self.product_id = self.order_lines.product_id