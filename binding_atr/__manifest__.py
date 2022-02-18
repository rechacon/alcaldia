{
    'name': 'Integración ATR',
    'version': '15.0.1.1.0',
    'author': 'Franyer Hidalgo - VE',
    'website': '',
    'contributors': [''],
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': 'ATR',
    'depends': ['base',
                'contacts'
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/atr_data.xml',
        'data/ir_cron.xml',
        'views/atr_views.xml',
        'views/partner_views.xml',
    ],
    'external_dependencies': {
        'python': ['psycopg2'],
    },
    'demo': [],
    'css': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False
}
