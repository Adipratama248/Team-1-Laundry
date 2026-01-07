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
    ],
    'data': [
        'security/laundry_security.xml',
        'security/ir.model.access.csv',
        'data/laundry_sequence.xml',
        'views/laundry_process_view.xml',
        'views/laundry_qc_view.xml',
        'views/laundry_order_view.xml',
        'views/sale_order_view.xml',
        # 'views/product_view.xml',
        'views/product_inherit.xml',
        'views/laundry_menu.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}


