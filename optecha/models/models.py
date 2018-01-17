# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from .constants import MAKE_DESIGN_HTML


class OptechaDesign(models.Model):
    _name = 'optecha.design'

    name = fields.Char('Design Name', required=False)
    project_name = fields.Char('Project Name', required=False)
    project_location = fields.Char('Project Location', required=False)
    project_completion_date = fields.Date('Expected Completion Date')
    revision_version = fields.Char("Revision version")
    status = fields.Selection([('ifr', 'IFR'), ('ifc', 'IFC')])
    # opportunity_name = fields.Char('Opportunity')

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



    """
    This selection field contains all the possible values for the statusbar.
    The first part is the database value, the second is the string that is showed. Example:
    ('finished','Done'). 'finished' is the database key and 'Done' the value shown to the user
    """
    state = fields.Selection([
        ('in_progress', 'Design In Progress'),
        ('team_review', 'Design Team Review'),
        ('customer_review', 'Customer Review'),
        ('done', 'Done')
        ], default='in_progress')

    # < p >${object.designer_id} < / p >
    # < p > Please
    # review
    # the ${object.name} ${object.opportunity_id}
    # design. < / p >
    @api.multi
    def team_review(self):
        template = self.env["mail.template"].search([("name", "=", "Team Review")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "opportunity_name": self.opportunity_id.name})
        lead_designer_id = self.env['res.groups'].search([('name', '=', 'Lead Designer')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'team_review',
        })

    @api.multi
    def customer_review(self):
        if self.opportunity_id.id:
            template = self.env["mail.template"].search([("name", "=", "Customer Review")])
            template.attachment_ids = [attachment.id for attachment in self.design_file]
            local_context = self.env.context.copy()
            local_context.update({"revision_no": self.revision_version,
                                  "opportunity_name": self.opportunity_id.name})
            template.with_context(local_context).send_mail(self.opportunity_id.partner_id.id, force_send=True)
        self.write({
            'state': 'customer_review',
        })

    @api.multi
    def done(self):
        template = self.env["mail.template"].search([("name", "=", "Design Approved By Customer")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "opportunity_name": self.opportunity_id.name})
        lead_designer_id = self.env['res.groups'].search([('name', '=', 'quote team member')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'done',
        })

    @api.multi
    def reset(self):
        template = self.env["mail.template"].search([("name", "=", "Design Rejected By Design Team")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "opportunity_name": self.opportunity_id.name})
        # lead_designer_id = self.env['res.groups'].search([('name', '=', 'Designer')]).id
        users = self.env["res.users"].search([("email", "=", self.designer_id[0].email)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'in_progress',
        })

    @api.multi
    def reset_by_customer(self):
        template = self.env["mail.template"].search([("name", "=", "Design Rejected By Customer")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "customer_name": self.env.user.name,
                              "opportunity_name": self.opportunity_id.name})
        # lead_designer_id = self.env['res.groups'].search([('name', '=', 'Designer')]).id
        users = self.env["res.users"].search([("email", "=", self.designer_id[0].email)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({
            'state': 'in_progress',
        })


class OptechaDrawing(models.Model):
    _name = 'optecha.drawing'
    name = fields.Char('Drawing Name', required=True)
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', track_visibility='onchange', index=True,
                                     help="Opportunity", required=True)
    quotation_id = fields.Many2one('sale.order', string='Quotation', track_visibility='onchange', index=True,
                                   help="Quotation", required=True)

    project_name = fields.Char('Project Name')
    revision_version = fields.Char('Revision Version')
    version = fields.Char('Drawing Version')
    state = fields.Selection([
        ('in_progress', 'Prepare Design'),
        ('approved', 'Approve Design'),
        ('issued_to_customer', 'Issued To Customer'),
        ('engineer_review', 'Engineer Drawing Review'),
        ('done', 'Approved')
        ], default='in_progress')

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
    def approved(self):
        self.write({
            'state': 'approved',
        })

    @api.multi
    def issued_to_customer(self):
        self.write({'state': 'issued_to_customer'
                    })

    @api.multi
    def engineer_review(self):
        self.write({'state': 'engineer_review'
                    })

    @api.multi
    def done(self):
        # approved
        template = self.env["mail.template"].search([("name", "=", "Drawing Approved By Drawing Team")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "drawing_team_member": self.env.user.name,
                              "opportunity_name": self.opportunity_id.name})
        lead_designer_id = self.env['res.groups'].search([('name', '=', 'Contractor')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
        for user in users:
            template.with_context(local_context).send_mail(user.id, force_send=True)
        self.write({'state': 'done'
                    })

    @api.multi
    def not_approved(self):
        # not approved
        template = self.env["mail.template"].search([("name", "=", "Drawing Not Approved By Contractor")])
        local_context = self.env.context.copy()
        local_context.update({"revision_no": self.revision_version,
                              "contractor": self.env.user.name,
                              "opportunity_name": self.opportunity_id.name})
        lead_designer_id = self.env['res.groups'].search([('name', '=', 'approval drawing team member')]).id
        users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
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


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    design_id = fields.One2many('optecha.design', "opportunity_id", 'Design', readonly=False)
    drawing_id = fields.One2many('optecha.drawing', "opportunity_id", "Drawing", readonly=False)
    quotation_id = fields.One2many('sale.order', "opportunity_id", "Drawing", readonly=True)
    select_design = fields.Many2one('optecha.design', string='Select Design', track_visibility='onchange', index=True,
                                    help="Design")
    project_name = fields.Char('Project Name')
    project_location = fields.Char('Project Location')
    revision_version = fields.Char('Revision version')
    project_completion_date = fields.Date('Expected Completion Date')

    @api.multi
    @api.onchange("stage_id")
    def on_change_stage_id(self):
        """

        :return:
        """
        if self.stage_id.name.lower() == "Make Design".lower():
            template = self.env["mail.template"].search([("name", "=", "Make Design")])
            lead_designer_id = self.env['res.groups'].search([('name', '=', 'Lead Designer')]).id
            users = self.env["res.users"].search([("groups_id", "=", lead_designer_id)])
            for user in users:
                template.send_mail(user.id, email_values={"body_html": MAKE_DESIGN_HTML.format(user.name, self.name)})


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


