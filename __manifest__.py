# -*- coding: utf-8 -*-
{
    'name': 'Laundry Management',
    'version': '18.0.1.0.0',
    'summary': 'Enterprise Laundry Management System',
    'description': 'Laundry management integrated with Sales, Inventory, Accounting, and HR.',
    'category': 'Services',
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'account',
        'stock',
        'product',
        'uom',
        'hr',
        'web',
        'purchase', 
        'contacts',
    ],

    'data': [
        'security/groups.xml',
        'security/rules.xml',
        # 'security/menu_restriction.xml',
        'security/ir.model.access.csv',

        'wizard/laundry_assign_operator.xml',
        'wizard/laundry_order_qc_wizard.xml',

        'data/laundry_sequence.xml',
        
        'views/laundry_qc_view.xml',
        'views/laundry_order_view.xml',
        'views/sale_order_view.xml',
        # 'views/product_view.xml',
        'views/product_inherit.xml',
        'views/laundry_log.xml',
        'views/laundry_menu.xml',

        'report/report_action.xml',
        'report/report_laundry_tag.xml',

    ],  
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}


