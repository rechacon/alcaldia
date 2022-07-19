{
    'name': 'Declaración de Impuestos',
    'version': '15.0.1.1.0',
    'author': 'Franyer Hidalgo - VE',
    'website': '',
    'contributors': [''],
    'category': 'Tools',
    'license': 'AGPL-3',
    'summary': 'ATR',
    'depends': ['base',
                'l10n_ve_currency_rate',
                ],
    'data': ['security/ir.model.access.csv',
             'data/ir_cron.xml',
             'views/tax_return_view.xml',
             'views/declaration_statistics_view.xml',
             'views/monthly_goal_view.xml',
             'views/indicators_view.xml',

             # Reports
             'report/report_municipal_comparison.xml',

             # Wizards
             'wizard/wizard_reports_view.xml',
             ],
    'demo': [],
    'css': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': False
}
