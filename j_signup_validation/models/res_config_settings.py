# -*- coding: utf-8 -*-
"""
Configuration Settings for J Signup Validation
Extends res.config.settings to add custom validation configuration options.
"""

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """
    Extend configuration settings to include custom validation options.
    """
    _inherit = 'res.config.settings'

    # Password Validation Settings
    restrict_user_password = fields.Boolean(
        'Restrict User Password',
        default=True,
        config_parameter='j_signup_validation.restrict_user_password',
        help='Enable user password strength restrictions'
    )
    
    password_min_length = fields.Integer(
        'Minimum Password Length',
        default=8,
        config_parameter='j_signup_validation.password_min_length',
        help='Minimum number of characters required in password'
    )
    
    password_require_number = fields.Boolean(
        'Require At Least One Number',
        default=True,
        config_parameter='j_signup_validation.password_require_number',
        help='Password must contain at least one numeric character'
    )
    
    password_require_uppercase = fields.Boolean(
        'Require At Least One Uppercase',
        default=False,
        config_parameter='j_signup_validation.password_require_uppercase',
        help='Password must contain at least one uppercase letter'
    )
    
    password_require_lowercase = fields.Boolean(
        'Require At Least One Lowercase',
        default=False,
        config_parameter='j_signup_validation.password_require_lowercase',
        help='Password must contain at least one lowercase letter'
    )
    
    password_require_special = fields.Boolean(
        'Require At Least One Special Symbol',
        default=False,
        config_parameter='j_signup_validation.password_require_special',
        help='Password must contain at least one special character'
    )
    
    # Email Validation Settings
    email_syntax_check = fields.Boolean(
        'Email Syntax Check',
        default=True,
        config_parameter='j_signup_validation.email_syntax_check',
        help='Validate email address syntax and format'
    )
    
    email_mx_verification = fields.Boolean(
        'MX Record Verification',
        default=True,
        config_parameter='j_signup_validation.email_mx_verification',
        help='Verify email domain has valid MX (Mail Exchange) records'
    )
    
    email_disposable_check = fields.Boolean(
        'Disposable Email Check',
        default=True,
        config_parameter='j_signup_validation.email_disposable_check',
        help='Block registration with temporary/disposable email addresses'
    )
    
    # Temp Mail Detection Method Settings
    temp_mail_detection_method = fields.Selection([
        ('library', 'Use Library (disposable_email_validator)'),
        ('api', 'Use TempMailDetector API')
    ], 'Temp Mail Detection Method',
        default='library',
        config_parameter='j_signup_validation.temp_mail_detection_method',
        help='Choose the method to detect temporary/disposable email addresses'
    )
    
    temp_mail_api_key = fields.Char(
        'TempMailDetector API Key',
        config_parameter='j_signup_validation.temp_mail_api_key',
        help='API key for TempMailDetector service (required when using API method)'
    )
    
    # Phone Validation Settings
    phone_validation_enabled = fields.Boolean(
        'Enable Phone Validation',
        default=True,
        config_parameter='j_signup_validation.phone_validation_enabled',
        help='Enable international phone number validation'
    )
    
    phone_require_mobile = fields.Boolean(
        'Require Mobile Numbers Only',
        default=False,
        config_parameter='j_signup_validation.phone_require_mobile',
        help='Only allow mobile phone numbers for registration'
    )
    
    # Registration Settings
    registration_require_email_verification = fields.Boolean(
        'Require Email Verification',
        default=False,
        config_parameter='j_signup_validation.registration_require_email_verification',
        help='Send verification email before activating account'
    )
    
    registration_auto_login = fields.Boolean(
        'Auto Login After Registration',
        default=True,
        config_parameter='j_signup_validation.registration_auto_login',
        help='Automatically log in user after successful registration'
    )

    @api.model
    def get_password_validation_rules(self):
        """
        Get current password validation rules as a dictionary.
        
        Returns:
            dict: Current password validation configuration
        """
        try:
            config = self.env['ir.config_parameter'].sudo()
            
            rules = {
                'enabled': config.get_param('j_signup_validation.restrict_user_password', 'True') == 'True',
                'min_length': int(config.get_param('j_signup_validation.password_min_length', '8')),
                'require_number': config.get_param('j_signup_validation.password_require_number', 'True') == 'True',
                'require_uppercase': config.get_param('j_signup_validation.password_require_uppercase', 'False') == 'True',
                'require_lowercase': config.get_param('j_signup_validation.password_require_lowercase', 'False') == 'True',
                'require_special': config.get_param('j_signup_validation.password_require_special', 'False') == 'True',
            }
            
            _logger.info(f"Retrieved password validation rules: {rules}")
            return rules
            
        except Exception as e:
            _logger.error(f"Error retrieving password validation rules: {str(e)}")
            # Return default rules on error
            return {
                'enabled': True,
                'min_length': 8,
                'require_number': True,
                'require_uppercase': False,
                'require_lowercase': False,
                'require_special': False,
            }

    @api.model
    def get_email_validation_rules(self):
        """
        Get current email validation rules as a dictionary.
        
        Returns:
            dict: Current email validation configuration
        """
        try:
            config = self.env['ir.config_parameter'].sudo()
            
            rules = {
                'syntax_check': config.get_param('j_signup_validation.email_syntax_check', 'True') == 'True',
                'mx_verification': config.get_param('j_signup_validation.email_mx_verification', 'True') == 'True',
                'disposable_check': config.get_param('j_signup_validation.email_disposable_check', 'True') == 'True',
            }
            
            _logger.info(f"Retrieved email validation rules: {rules}")
            return rules
            
        except Exception as e:
            _logger.error(f"Error retrieving email validation rules: {str(e)}")
            # Return default rules on error
            return {
                'syntax_check': True,
                'mx_verification': True,
                'disposable_check': True,
            }

    @api.model
    def get_phone_validation_rules(self):
        """
        Get current phone validation rules as a dictionary.
        
        Returns:
            dict: Current phone validation configuration
        """
        try:
            config = self.env['ir.config_parameter'].sudo()
            
            rules = {
                'validation_enabled': config.get_param('j_signup_validation.phone_validation_enabled', 'True') == 'True',
                'require_mobile': config.get_param('j_signup_validation.phone_require_mobile', 'False') == 'True',
            }
            
            _logger.info(f"Retrieved phone validation rules: {rules}")
            return rules
            
        except Exception as e:
            _logger.error(f"Error retrieving phone validation rules: {str(e)}")
            # Return default rules on error
            return {
                'validation_enabled': True,
                'require_mobile': False,
            }

    def validate_password_strength(self, password):
        """
        Validate password strength based on current configuration.
        
        Args:
            password (str): Password to validate
            
        Returns:
            dict: Validation result with score and messages
        """
        rules = self.get_password_validation_rules()
        
        if not rules.get('enabled', True):
            return {'valid': True, 'score': 100, 'messages': []}
        
        messages = []
        score = 0
        
        # Check minimum length
        if len(password) >= rules.get('min_length', 8):
            score += 25
        else:
            messages.append(f"Password must be at least {rules.get('min_length', 8)} characters long")
        
        # Check for numbers
        if rules.get('require_number', True):
            if any(char.isdigit() for char in password):
                score += 25
            else:
                messages.append("Password must contain at least one number")
        else:
            score += 25
        
        # Check for uppercase
        if rules.get('require_uppercase', False):
            if any(char.isupper() for char in password):
                score += 25
            else:
                messages.append("Password must contain at least one uppercase letter")
        else:
            score += 25
        
        # Check for lowercase
        if rules.get('require_lowercase', False):
            if any(char.islower() for char in password):
                score += 25
            else:
                messages.append("Password must contain at least one lowercase letter")
        else:
            score += 25
        
        # Check for special characters
        if rules.get('require_special', False):
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if any(char in special_chars for char in password):
                score += 0  # Already accounted for in previous checks
            else:
                messages.append("Password must contain at least one special character")
                score -= 25
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return {
            'valid': len(messages) == 0,
            'score': score,
            'messages': messages
        }