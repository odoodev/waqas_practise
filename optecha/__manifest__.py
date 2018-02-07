# -*- coding: utf-8 -*-
{
    'name': "optecha",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail','sale_management', 'crm', 'sale_crm','purchase'],

    # always loaded
    'data': [
        'demo/demo.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/rma.xml',
        'report/optecha_report.xml',
        'report/optecha_sale_report_temp.xml',
        'data/designer_template.xml',
        'views/templates.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}