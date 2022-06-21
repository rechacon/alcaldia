{
    "name": "Localización Venezolana: Nómina Empresa Publica",
    "version": "15.0.1",
    "author": "Franyer H. VE / Jean C. VE",
    "category": "Localization",
    'contributors': ['Franyer Hidalgo <fhidalgo.dev@gmail.com>',
                     'Jean Castro VE <jeancastro.developerve@gmail.com>'],
    "website": "",
    'images': ['static/description/icon.png'],
    "depends": ['base', 'hr_payroll', 'hr_contract', 'hr'],
    "init_xml": [],
    "demo_xml": [],
    'external_dependencies': {},
    "data": ['security/ir.model.access.csv',
             'data/data_academic_degree.xml',
             'data/data_sector_laboral.xml',
             'data/ir.cron.xml',
             'views/hr_incentives_views.xml',
             'views/res_company_views.xml',
             'views/hr_job_views.xml',
             'views/hr_employee_views.xml',
             'views/hr_contract_views.xml'],
    "installable": True,
    'license': 'LGPL-3',
}
