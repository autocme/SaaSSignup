# -*- coding: utf-8 -*-
{
    'name': 'J Signup Validation',
    'version': '17.0.1.0.0',
    'category': 'Authentication',
    'summary': 'Custom user registration with advanced email/phone/password validation',
    'description': """
        Comprehensive Odoo 17 module for custom user registration featuring:
        - Custom SaaS User model for data storage
        - Advanced password strength validation with real-time progress bar
        - Email validation with syntax, MX records, and disposable email checks
        - International phone number validation
        - Elegant, modern registration form design
        - Configurable validation rules in General Settings
        - Dual user creation (SaaS User + Portal User)
    """,
    'author': 'J Signup Validation',
    'website': 'https://www.example.com',
    'depends': [
        'base',
        'auth_signup',
        'portal',
        'base_setup',
        'mail',
    ],
    'external_dependencies': {
        'python': [
            'verify-email',
            'disposable-email-validator',
            'phonenumbers',
            'dnspython',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/auth_login_templates.xml',
        'views/saas_user_views.xml',
        'views/res_users_views.xml',
        'views/res_config_settings_views.xml',
        'views/signup_configuration_views.xml',
        'data/mail_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'j_signup_validation/static/src/css/j_signup_unique.css',
            'j_signup_validation/static/src/js/password_strength.js',
            'j_signup_validation/static/src/js/signup_validation.js',
            'j_signup_validation/static/src/js/country_phone_selector.js',
        ],
        'web.assets_backend': [
            'j_signup_validation/static/src/css/j_signup_unique.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}