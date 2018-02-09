# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RmaForm(models.Model):
    _name = 'optecha.rma'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'format.address.mixin']

    name = fields.Char("RMA")
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    orders = fields.Many2one('sale.order', string="Order", domain="[('opportunity_id','=',opportunity_id)]")
    order_lines = fields.Many2one('sale.order.line', string="Order Line",
                                  domain="[('order_id','=',orders)]")
    reason = fields.Text(string="Reasons")
    partner_id = fields.Many2one('res.partner', string="Customer")
    product_id = fields.Many2one('product.product', string="Product", store=True)
    state = fields.Selection([
        ('fixtures', 'Fixture Failure'),
        ('contact_manufacturer', 'Contact Manufacturer'),
        ('quote_to_customer', 'Quote To Customer'),
        ('customer_issue_po', 'Customer Issue Po'),
        ('issue_po_to_manufacture', 'Issue Po To Manufacture'),
        ('customer_receive_product', 'Customer Receives Product'),
        ('return_fixture', 'Return Fixture For Inspection'),
        ('manufacturer_approval', 'Manufacturer Approval'),
        ('issue_credit_to_customer', 'Issue Credit To Customer'),
        ('issue_invoice_to_customer', 'Issue Invoice To Customer'),
        ('done', 'Done')
    ], default='fixtures')
    quantity = fields.Integer(String="Quantity")

    @api.onchange('order_lines')
    def _onchange_order_lines(self):
        self.product_id = self.order_lines.product_id

    @api.onchange('opportunity_id')
    def _onchange_opportunity(self):
        self.partner_id = self.opportunity_id.partner_id
        self.orders = False
        self.order_lines = False
        self.product_id = False

    @api.multi
    def contact_manufacturer(self):
        self.write({
            'state': 'contact_manufacturer',
        })

    @api.multi
    def quote_to_customer(self):
        self.write({
            'state': 'quote_to_customer',
        })

    @api.multi
    def customer_issue_po(self):
        self.write({
            'state': 'customer_issue_po',
        })

    @api.multi
    def issue_po_to_manufacture(self):
        self.write({
            'state': 'issue_po_to_manufacture',
        })

    @api.multi
    def customer_receive_product(self):
        self.write({
            'state': 'customer_receive_product',
        })

    @api.multi
    def return_fixture(self):
        self.write({
            'state': 'return_fixture',
        })