from odoo import models, fields, api, _
from werkzeug.urls import url_encode
from odoo.osv import osv


class OptechaDrawing(models.Model):
    _name = 'optecha.fixture_failure'
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