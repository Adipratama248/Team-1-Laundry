# -*- coding: utf-8 -*-
{
    'name': "laundry",

    'summary': "Laundry Services Management",

    'description': """
Module for managing laundry services with master data for various laundry products.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/laundry_service.xml',
    ],
}

