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
    po_order = fields.One2many('purchase.order', "opportunity_id", "Purchase Orders", readonly=True)
    quotation_id = fields.One2many('sale.order', "opportunity_id", "Quotation", readonly=True)
    order_lines_ids = fields.One2many('total.orderd.product','order_id',"Order Lines")
    team_id = fields.Many2one('crm.team','Sales Channel')
    user_id = fields.Many2one('res.users','Salesperson')
    shipping_ref = fields.Char('Shipping Reference')
    #
    # @api.onchange('order_lines')
    # def _onchange_order_lines(self):
    #     self.team_id = self.order_lines.team_id
    #     self.user_id = self.order_lines.user_id

    @api.onchange('orders')
    def onchange_orders(self):
        # self.order_lines_ids.unlink()
        total_so = []
        for order in self.orders.order_line:
            group = self.env['total.orderd.product'].create({
                "name": order.name,
                "deliver_qty": order.product_uom_qty,
                "product_uom": order.product_uom.name,
            })
            total_so.append(group.id)
        self.order_lines_ids = [(6, 0, total_so)]
        self.team_id = self.orders.team_id
        self.user_id = self.orders.user_id
        # self.shipping_ref = self.orders.action_view_delivery.im_self.picking_ids.name

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
    def back(self):
        if self.state == "contact_manufacturer":
            self.write({
                'state' : 'fixtures'
            })
        elif self.state == "quote_to_customer":
            self.write({
                'state' : 'contact_manufacturer'
            })
        elif self.state == "customer_issue_po":
            self.write({
                'state' : 'quote_to_customer'
            })
        elif self.state == "issue_po_to_manufacture":
            self.write({
                'state' : 'customer_issue_po'
            })
        elif self.state == "customer_receive_product":
            self.write({
                'state' : 'issue_po_to_manufacture'
            })
        elif self.state == "return_fixture":
            self.write({
                'state' : 'customer_receive_product'
            })
        elif self.state == "manufacturer_approval":
            self.write({
                'state' : 'return_fixture'
            })
        elif self.state == "issue_credit_to_customer":
            self.write({
                'state' : 'manufacturer_approval'
            })
        elif self.state == "issue_invoice_to_customer":
            self.write({
                'state' : 'manufacturer_approval'
            })

    @api.multi
    def quote_to_customer(self):
        self.write({
            'state': 'quote_to_customer',
        })

    @api.multi
    def customer_issue_po(self):
        # if len(self.order_lines_ids)==0:
        #     raise
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

    @api.multi
    def manufacturer_approval(self):
        self.write({
            'state': 'manufacturer_approval',
        })

    @api.multi
    def issue_credit_to_customer(self):
        self.write({
            'state': 'done',
        })

    @api.multi
    def issue_invoice_to_customer(self):
        self.write({
            'state': 'done',
        })

    @api.multi
    def done(self):
        self.write({
            'state': 'done',
        })
    # @api.multi
    # def sale_action_qu(self):
    #     self.ensure_one()
    #     action = self.env.ref('sale.action_product_sale_list')
    #     # product_ids = self.with_context(active_test=False).product_variant_ids.ids
    #
    #     return {
    #         'name': action.name,
    #         'help': action.help,
    #         'type': action.type,
    #         'view_type': action.view_type,
    #         'view_mode': action.view_mode,
    #         'target': action.target,
    #         # 'context': "{'default_opportunity_id': " + str(self.opportunity_id) + "}",
    #         'res_model': action.res_model,
    #         'domain': [('state', 'in', ['sale', 'done']), ('product_id.product_tmpl_id', '=', self.id)],
    #     }


class RmaProducts(models.Model):
    _name = "total.orderd.product"

    name = fields.Char('Return Product')
    deliver_qty = fields.Char('Deliver Quantity')
    return_qty = fields.Char('Return Request Quantity')
    product_uom = fields.Char('Product Uom')
    select = fields.Boolean('Active')
    order_id = fields.Many2one('optecha.rma')


# class SaleRma(models.Model):
#     _name = "sale.rmass"
#     _inherit ="sale.order"
#
#     def create(self, values):
#         print ("Raja g")
#
#         return super(SaleRma, self).create(values)
