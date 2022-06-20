{
    "name": "Localización Venezolana: Exchange Rate",
    "version": "14.0.1",
    "author": "Franyer H. VE / Jean C. VE",
    "category": "Localization",
    'contributors': ['Franyer Hidalgo <fhidalgo.dev@gmail.com>',
                     'Jean Castro VE <jeancastro.developerve@gmail.com>'],
    "website": "",
    'images': ['static/description/icon.png'],
    "depends": ['base',
                'account',
                ],
    "init_xml": [],
    "demo_xml": [],
    'external_dependencies': {
        'python': ['beautifulsoup4'],
    },
    "data": [
        'views/res_currency_views.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
    ],
    "installable": True
}
