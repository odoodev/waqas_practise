# -*- coding: utf-8 -*-
from werkzeug.urls import url_encode
from odoo import models, fields, api, _
from odoo.osv import osv
from odoo.exceptions import UserError, AccessError


class OptechaDesign(models.Model):
    _name = 'optecha.design'

    name = fields.Char('Design Name', required=False)
    project_name = fields.Char('Project Name', required=False)
    project_location = fields.Char('Project Location', required=False)
    project_completion_date = fields.Date('Expected Completion Date')
    revision_version = fields.Char("Revision version")
    status = fields.Selection([('ifr', 'IFR'), ('ifc', 'IFC')])
    state_date = fields.Datetime(default=fields.Datetime.now, store=True)
    no_of_days = fields.Float(compute='_compute_no_of_days', string='Number of Days', store=True)

    @api.model
    def _get_designer_id(self):
        return [('groups_id', '=', self.env['res.groups'].search([('name', '=', 'Designer')]).id)]

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', track_visibility='onchange', index=True,
                                     help="Opportunity", required=True)
    designer_id = fields.Many2one('res.users', string='Designer', track_visibility='onchange', index=True,
                                  help="Desiger, odoo user", required=True, domain=_get_designer_id)
    architect_id = fields.Many2one('res.users', string='Architect', track_visibility='onchange', index=True,
                                   help="Desiger, odoo user", required=False)
    design_file = fields.Many2many('ir.attachment', 'optechadesign_ir_attachments_rel',
                                   'optechadesign_id', 'attachment_id', 'Attachments')

    state = fields.Selection([
        ('in_progress', 'Design In Progress'),
        ('team_review', 'Design Team Review'),
        ('customer_review', 'Customer Review'),
        ('done', 'Done')
        ], default='in_progress')

    @api.depends("state_date")
    def _compute_no_of_days(self):
        """ Compute difference between current date and log date """
        for design in self:
            state_date_time = fields.Datetime.from_string(design.state_date)
            current_date_time = fields.Datetime.from_string(fields.Datetime.now())
            design.no_of_days = abs(current_date_time - state_date_time).days

    @api.model
    def create(self, values):
        """

        :param values:
        :return:
        """
        record = super(OptechaDesign, self).create(values)
        template = self.env["mail.template"].search([("name", "=", "Prepare Design")])
        local_context = self.env.context.copy()
        local_context.update({"design_name": values["name"],
                              "share_url": self.get_share_url(record.id)})
        template.with_context(local_context).send_mail(values["designer_id"], force_send=True)
        return record

    @api.multi
    def team_review(self):
        self.update_no_of_days()
        template = self.env["mail.template"].search([("name", "=", "Team Review")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "opportunity_name": self.opportunity_id.name,
                              "share_url": self.get_share_url()})
        lead_designer_id = self.env['res.groups'].search([('name', '=', 'Lead Designer')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'team_review',
        })
        self.state_date = fields.Datetime.now()

    @api.multi
    def customer_review(self):
        # if self.opportunity_id.id:
        #     template = self.env["mail.template"].search([("name", "=", "Customer Review")])
        #     template.attachment_ids = None
        #     template.attachment_ids = [attachment.id for attachment in self.design_file]
        #     local_context = self.env.context.copy()
        #     local_context.update({"revision_no": self.revision_version,
        #                           "opportunity_name": self.opportunity_id.name})
        #     template.with_context(local_context).send_mail(self.opportunity_id.partner_id.id, force_send=True)
        self.write({
            'state': 'customer_review',
        })
        self.state_date = fields.Datetime.now()
 
    @api.multi
    def done(self):
        template = self.env["mail.template"].search([("name", "=", "Design Approved By Customer")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "opportunity_name": self.opportunity_id.name,
                              "share_url": self.get_share_url()})
        lead_designer_id = self.env['res.groups'].search([('name', '=', 'quote team member')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'done',
        })
        self.state_date = fields.Datetime.now()

    @api.multi
    def reject_reset(self):
        template = self.env["mail.template"].search([("name", "=", "Design Rejected By Design Team")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "opportunity_name": self.opportunity_id.name,
                              "share_url": self.get_share_url()})
        # lead_designer_id = self.env['res.groups'].search([('name', '=', 'Designer')]).id
        users = self.env["res.users"].search([("email", "=", self.designer_id[0].email)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'in_progress',
        })
        self.state_date = fields.Datetime.now()

    @api.multi
    def reset(self):
        # template = self.env["mail.template"].search([("name", "=", "Design Rejected By Design Team")])
        # local_context = self.env.context.copy()
        # local_context.update({"revision_no": self.revision_version,
        #                       "opportunity_name": self.opportunity_id.name,
        #                       "share_url": self.get_mail_url()})
        # # lead_designer_id = self.env['res.groups'].search([('name', '=', 'Designer')]).id
        # users = self.env["res.users"].search([("email", "=", self.designer_id[0].email)])
        # for user in users:
        #     template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'in_progress',
        })
        self.state_date = fields.Datetime.now()

    @api.multi
    def reset_by_customer(self):
        template = self.env["mail.template"].search([("name", "=", "Design Rejected By Customer")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "customer_name": self.env.user.name,
                              "opportunity_name": self.opportunity_id.name,
                              "share_url": self.get_share_url()})
        # lead_designer_id = self.env['res.groups'].search([('name', '=', 'Designer')]).id
        users = self.env["res.users"].search([("email", "=", self.designer_id[0].email)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'in_progress',
        })
        self.state_date = fields.Datetime.now()

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edit sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('optecha', 'example_email_template')[1]

        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        template = self.env["mail.template"].search([("name", "=", "Customer Review")])
        template.attachment_ids = None
        template.attachment_ids = [attachment.id for attachment in self.design_file]

        ctx = {
            'default_model': 'optecha.design',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'design_file': self.env.context.get('design_file', False),
            'force_email': True,
            'revision_no': self.revision_version,
            'opportunity_name': self.opportunity_id.name,
            'customer_name': self.opportunity_id.partner_id.name,
            'customer_email': self.opportunity_id.partner_id.email

        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def get_share_url(self, id=None):
        # self.ensure_one()
        params = {
            'model': self._name,
            'res_id': id if id else self.id,
        }
        if hasattr(self, 'access_token') and self.access_token:
            params['access_token'] = self.access_token
        if hasattr(self, 'partner_id') and self.partner_id:
            params.update(self.partner_id.signup_get_auth_param()[self.partner_id.id])

        return '/mail/view?' + url_encode(params)

    def update_no_of_days(self):
        """

        :return:
        """
        all_object = self.env["optecha.design"].search([])
        for obj in all_object:
            obj._compute_no_of_days()


class OptechaDrawing(models.Model):
    _name = 'optecha.drawing'
    name = fields.Char('Drawing Name', required=True)
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', track_visibility='onchange', index=True,
                                     help="Opportunity", required=True)
    quotation_id = fields.Many2one('sale.order', string='Quotation', track_visibility='onchange', index=True,
                                   help="Quotation", required=True)

    design_file = fields.Many2many('ir.attachment', 'optechadesign_ir_attachments_rel',
                                   'optechadesign_id', 'attachment_id', 'Attachments')

    project_name = fields.Char('Project Name')
    revision_version = fields.Char('Revision Version')
    version = fields.Char('Drawing Version')
    contractor_id = fields.Many2one('res.users')
    assign_to = fields.Many2one('res.users')
    comment = fields.Text(string="Review Comments")
    state = fields.Selection([
        ('in_progress', 'Prepare Approval Drawing Package'),
        ('team_review', 'Optecha Review Approval Drawing Package'),
        ('engineer_review', 'Contractor/Engineer Review Approval Drawing Package'),
        ('done', 'Done'),
        ('out_to_date', 'Out To Date')
    ], default='in_progress')

    @api.model
    def create(self, values):
        """

        :param values:
        :return:
        """
        record = super(OptechaDrawing, self).create(values)
        template = self.env["mail.template"].search([("name", "=", "Prepare Drawing")])
        local_context = self.env.context.copy()
        local_context.update({"drawing_name": values["name"],
                              "share_url": self.get_share_url(record.id)})
        template.with_context(local_context).send_mail(values["assign_to"], force_send=True)
        return record

    @api.onchange("quotation_id")
    def insert_data(self):
        self.project_name = self.quotation_id.project_name
        self.revision_version = self.quotation_id.select_design.revision_version

    @api.multi
    def in_progress(self):
        self.write({
            'state': 'in_progress',
        })

    @api.multi
    def team_review(self):
        template = self.env["mail.template"].search([("name", "=", "Drawing Team Review")])
        local_context = self.env.context.copy()
        local_context.update({"drawing_version": self.version,
                              "drawing_name": self.name,
                              "opportunity_name": self.opportunity_id.name,
                              "share_url": self.get_share_url()})
        lead_drawing_id = self.env['res.groups'].search([('name', '=', 'Drawing Team Lead')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_drawing_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)

        self.write({
            'state': 'team_review',
        })

    @api.multi
    def engineer_review(self):
        self.write({'state': 'engineer_review'
                    })

    @api.multi
    def team_reject(self):
        if self.comment != '<p><br></p>':
            template = self.env["mail.template"].search([("name", "=", "Drawing Rejected By Team")])
            temp = template["body_html"]
            temporary = template["body_html"].split("adha_kr_dy")
            # as format and other specifier % for string were not working.
            template["body_html"] = temporary[0] + self.comment + temporary[1]
            local_context = self.env.context.copy()
            local_context.update({"drawing_version": self.version,
                                  "drawing_name": self.name,
                                  "opportunity_name": self.opportunity_id.name,
                                  "share_url": self.get_share_url()})
            template.with_context(local_context).send_mail(self.assign_to.id, force_send=True)
            template["body_html"] = temp
            self.write({
                'state': 'in_progress',
            })
        else:
            raise osv.except_osv(('Error'), ('Kindly mention reasons of rejection in Review Comments box'))

    @api.multi
    def done(self):
        self.write({'state': 'done'
                    })

    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_ids = ir_model_data.get_object_reference('optecha', 'drawing_email_template')
            template_id = template_ids[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        template = self.env[template_ids[0]].search([("id", "=", template_ids[1])])
        template.attachment_ids = None
        template.attachment_ids = [attachment.id for attachment in self.design_file]

        ctx = {
            'default_model': 'optecha.drawing',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'design_file': self.env.context.get('design_file', False),
            'force_email': True,
            'revision_no': self.revision_version,
            'opportunity_name': self.opportunity_id.name,
            'customer_name': self.opportunity_id.partner_id.name,
            'customer_email': self.opportunity_id.partner_id.email,
            'drawing_team_member': self.env.user.name,
            'contractor': self.contractor_id.email

        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def get_share_url(self, id=None):
        # self.ensure_one()
        params = {
            'model': self._name,
            'res_id': id if id else self.id
        }
        if hasattr(self, 'access_token') and self.access_token:
            params['access_token'] = self.access_token
        if hasattr(self, 'partner_id') and self.partner_id:
            params.update(self.partner_id.signup_get_auth_param()[self.partner_id.id])

        return '/mail/view?' + url_encode(params)

    @api.multi
    def rejected_by_contractor(self):
        # not approved
        template = self.env["mail.template"].search([("name", "=", "Drawing Rejected By Contractor")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "contractor": self.env.user.name,
                              "opportunity_name": self.opportunity_id.name,
                              "share_url": self.get_share_url()})
        drawing_lead_id = self.env['res.groups'].search([('name', '=', 'Drawing Team Lead')]).id
        users = self.env["res.users"].search([("groups_id", "=", drawing_lead_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'in_progress',
        })

    @api.multi
    def reset(self):
        self.write({
            'state': 'in_progress',
        })

    @api.multi
    def out_to_date(self):
        self.write({
            'state': 'out_to_date',
        })

    @api.multi
    def back_to_done(self):
        self.write({
            'state': 'done',
        })


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    quotation_fees_id = fields.One2many('sale.order', "opportunity_id", "Design Fees", readonly=True)
    po_order = fields.One2many('purchase.order', "opportunity_id", "Purchase Orders", readonly=True)
    design_id = fields.One2many('optecha.design', "opportunity_id", 'Design', readonly=False)
    drawing_id = fields.One2many('optecha.drawing', "opportunity_id", "Drawing", readonly=False)
    quotation_id = fields.One2many('sale.order', "opportunity_id", "Quotation", readonly=True)
    select_design = fields.Many2one('optecha.design', string='Select Design', track_visibility='onchange', index=True,
                                    help="Design")
    project_name = fields.Char('Project Name')
    project_location = fields.Char('Project Location')
    revision_version = fields.Char('Revision version')
    project_completion_date = fields.Date('Expected Completion Date')
    distributor_id = fields.Many2one('res.partner', string="Distributor Name", domain="[('category_id','=','Distributor')]")
    distributor_active = fields.Boolean('Active Distributor')

    @api.multi
    @api.onchange("stage_id")
    def on_change_stage_id(self):
        """

        :return:
        """
        if self.stage_id.name.lower() == "Design".lower():
            template = self.env["mail.template"].search([("name", "=", "Make Design")])
            local_context = self.env.context.copy()
            local_context.update({"opportunity_name": self.name})
            lead_designer_id = self.env['res.groups'].search([('name','=', 'Lead Designer')]).id
            users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
            for user in users:
                template.with_context(local_context).send_mail(user.id)


class OptechaProducts(models.Model):
    _inherit = 'product.template'

    product_category = fields.Char('Product Category', required=False)
    mounting = fields.Char('Mounting', required=False)
    size = fields.Char('Size')
    optic_distribution = fields.Char('Optic Distribution')
    optic_finish_option = fields.Char('Optic Finish Option')
    color_temperature = fields.Char('Color Temperature', required=False)
    normal_lumens_output = fields.Char('Normal Lumens Output', required=False)
    dimming = fields.Char('Dimming')
    wattage = fields.Char('Wattage', required=False)
    voltage = fields.Char('Voltage', required=False)
    color_finish = fields.Char('Color Finish')
    list_of_options = fields.Char('List of Options')
    application = fields.Selection([
        ('indoor', 'Indoor'),
        ('exterior', 'Exterior')]
        , string='Application')
    optecha_direct = fields.Selection([
        ('y', 'Y'),
        ('n', 'N')]
        , string='Optecha Direct')
    catalogue_number = fields.Char('Catalogue Number')
    # application = fields.Char("Application")


class OptechaQuotation(models.Model):
    _inherit = 'sale.order'

    dis_id = fields.Many2many('res.partner.category',"Distributor", related="partner_id.category_id")
    project_name = fields.Char("Project_name")
    project_location = fields.Char("Project_location")
    project_completion_date = fields.Date('Expected Completion Date')
    select_design = fields.Many2one('optecha.design', string='Select Design', track_visibility='onchange', index=True,
                                    help="Design")

    # @api.multi
    # def action_confirm(self):
    #
    #     self._action_confirm()
    #     if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
    #         self.action_done()
    #     return True

    @api.onchange("select_design")
    def insert_data(self):
        self.project_name = self.select_design.project_name
        self.project_location = self.select_design.project_location
        self.project_completion_date = self.select_design.project_completion_date


class OptechaSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    optecha_type = fields.Char('Type')


class OptechaPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order'

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', track_visibility='onchange', index=True,
                                     help="Opportunity")
    dis_id = fields.Many2many('res.partner.category',"Distributor", related="partner_id.category_id")
