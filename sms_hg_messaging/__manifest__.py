{
    'name': 'Integración con Hg Messaging (SMS)',
    'version': '14.0.1.1.0',
    'author': 'Franyer Hidalgo - VE',
    'website': '',
    'contributors': [''],
    'category': 'Hidden/Tools',
    'license': 'AGPL-3',
    'summary': 'Hg Messaging-SMS',
    'depends': ['base',
                'sms',
                'phone_validation',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/sms_views.xml',
        'wizards/sms_composer_views.xml',
        'views/partner_views.xml',
    ],
    'external_dependencies': {
        'python': ['suds-py3'],
    },
    'demo': [],
    'css': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False
}
