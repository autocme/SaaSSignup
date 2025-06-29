# -*- coding: utf-8 -*-
"""
Authentication and Signup Controllers
Custom controllers for handling user registration with advanced validation.
"""

import json
import logging
import re
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError
from werkzeug.exceptions import BadRequest

# External validation libraries
try:
    from verify_email import verify_email
    from disposable_email_validator import is_disposable
    import phonenumbers
    from phonenumbers import NumberParseException
except ImportError as e:
    logging.getLogger(__name__).warning(f"Missing validation libraries: {str(e)}")
    verify_email = None
    is_disposable = None
    phonenumbers = None

_logger = logging.getLogger(__name__)


class CustomAuthSignup(http.Controller):
    """
    Custom authentication controller for handling signup with validation.
    """

    @http.route('/j_signup_validation/test', type='http', auth='public', csrf=False)
    def test_route(self, **kw):
        """Test route to verify controller is working."""
        return "Custom signup controller is working!"

    @http.route('/j_signup_validation/signup', type='http', auth='public', csrf=False)
    def web_auth_signup(self, **kw):
        """
        Display custom signup form.
        """
        try:
            _logger.info("Accessing custom signup form")
            
            # Get validation rules for frontend
            config_settings = request.env['res.config.settings']
            password_rules = config_settings.get_password_validation_rules()
            email_rules = config_settings.get_email_validation_rules()
            phone_rules = config_settings.get_phone_validation_rules()
            
            # Get countries for phone number selection
            countries = request.env['res.country'].sudo().search([
                ('phone_code', '!=', False)
            ], order='name')
            
            # Prepare context for template
            values = {
                'password_rules': password_rules,
                'email_rules': email_rules,
                'phone_rules': phone_rules,
                'countries': countries,
                'error': kw.get('error', ''),
                'success': kw.get('success', ''),
            }
            
            return request.render('j_signup_validation.custom_signup_form', values)
            
        except Exception as e:
            _logger.error(f"Error loading signup form: {str(e)}")
            return request.render('web.login', {'error': _('Unable to load signup form. Please try again.')})

    @http.route('/j_signup_validation/submit', type='http', auth='public', methods=['POST'], csrf=False)
    def web_auth_signup_submit(self, **post):
        """
        Process signup form submission with validation.
        """
        try:
            _logger.info(f"Processing signup submission for email: {post.get('email')}")
            
            # Extract form data
            form_data = self._extract_form_data(post)
            
            # Validate all form fields
            validation_result = self._validate_signup_data(form_data)
            
            if not validation_result['valid']:
                _logger.warning(f"Signup validation failed: {validation_result['errors']}")
                return self._redirect_with_error(validation_result['errors'])
            
            # Create SaaS user and portal account
            saas_user, portal_user = self._create_user_accounts(form_data, validation_result)
            
            # Auto-login if configured
            if self._should_auto_login():
                self._auto_login_user(portal_user)
                return request.redirect('/web')
            else:
                return self._redirect_with_success(_('Registration successful! Please check your email for verification.'))
                
        except ValidationError as e:
            _logger.error(f"Validation error during signup: {str(e)}")
            return self._redirect_with_error(str(e))
        except Exception as e:
            _logger.error(f"Unexpected error during signup: {str(e)}")
            return self._redirect_with_error(_('Registration failed. Please try again.'))

    @http.route('/j_signup_validation/validate_email', type='json', auth='public')
    def validate_email_ajax(self, email):
        """
        AJAX endpoint for real-time email validation.
        """
        try:
            _logger.info(f"Validating email via AJAX: {email}")
            
            config_settings = request.env['res.config.settings']
            email_rules = config_settings.get_email_validation_rules()
            
            validation_result = self._validate_email(email, email_rules)
            
            return {
                'valid': validation_result['valid'],
                'messages': validation_result['messages']
            }
            
        except Exception as e:
            _logger.error(f"Error in AJAX email validation: {str(e)}")
            return {
                'valid': False,
                'messages': [_('Email validation service temporarily unavailable')]
            }

    @http.route('/j_signup_validation/validate_phone', type='json', auth='public')
    def validate_phone_ajax(self, phone):
        """
        AJAX endpoint for real-time phone validation.
        """
        try:
            _logger.info(f"Validating phone via AJAX: {phone}")
            
            config_settings = request.env['res.config.settings']
            phone_rules = config_settings.get_phone_validation_rules()
            
            validation_result = self._validate_phone(phone, phone_rules)
            
            return {
                'valid': validation_result['valid'],
                'messages': validation_result['messages'],
                'formatted': validation_result.get('formatted', phone)
            }
            
        except Exception as e:
            _logger.error(f"Error in AJAX phone validation: {str(e)}")
            return {
                'valid': False,
                'messages': [_('Phone validation service temporarily unavailable')]
            }

    @http.route('/j_signup_validation/validate_password', type='json', auth='public')
    def validate_password_ajax(self, password):
        """
        AJAX endpoint for real-time password strength validation.
        """
        try:
            _logger.info("Validating password strength via AJAX")
            
            config_settings = request.env['res.config.settings']
            validation_result = config_settings.validate_password_strength(password)
            
            return {
                'valid': validation_result['valid'],
                'score': validation_result['score'],
                'messages': validation_result['messages']
            }
            
        except Exception as e:
            _logger.error(f"Error in AJAX password validation: {str(e)}")
            return {
                'valid': False,
                'score': 0,
                'messages': [_('Password validation service temporarily unavailable')]
            }

    def _extract_form_data(self, post):
        """
        Extract and sanitize form data from POST request.
        """
        return {
            'first_name': post.get('first_name', '').strip(),
            'last_name': post.get('last_name', '').strip(),
            'email': post.get('email', '').strip().lower(),
            'phone': post.get('phone', '').strip(),
            'phone_country': post.get('phone_country', ''),
            'password': post.get('password', ''),
            'confirm_password': post.get('confirm_password', ''),
            'registration_ip': request.httprequest.environ.get('REMOTE_ADDR'),
            'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
        }

    def _validate_signup_data(self, form_data):
        """
        Comprehensive validation of signup data.
        """
        errors = []
        email_validation = {'valid': False}
        phone_validation = {'valid': False}
        password_validation = {'valid': False, 'score': 0}
        
        # Basic field validation
        if not form_data['first_name']:
            errors.append(_('First name is required'))
        if not form_data['last_name']:
            errors.append(_('Last name is required'))
        if not form_data['email']:
            errors.append(_('Email address is required'))
        if not form_data['phone']:
            errors.append(_('Phone number is required'))
        if not form_data['password']:
            errors.append(_('Password is required'))
        if form_data['password'] != form_data['confirm_password']:
            errors.append(_('Passwords do not match'))
        
        # Email validation
        if form_data['email']:
            config_settings = request.env['res.config.settings']
            email_rules = config_settings.get_email_validation_rules()
            email_validation = self._validate_email(form_data['email'], email_rules)
            if not email_validation['valid']:
                errors.extend(email_validation['messages'])
        
        # Phone validation
        if form_data['phone']:
            config_settings = request.env['res.config.settings']
            phone_rules = config_settings.get_phone_validation_rules()
            phone_validation = self._validate_phone(form_data['phone'], phone_rules, form_data.get('phone_country'))
            if not phone_validation['valid']:
                errors.extend(phone_validation['messages'])
        
        # Password validation
        if form_data['password']:
            config_settings = request.env['res.config.settings']
            password_validation = config_settings.validate_password_strength(form_data['password'])
            if not password_validation['valid']:
                errors.extend(password_validation['messages'])
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'password_score': password_validation.get('score', 0),
            'email_validated': email_validation.get('valid', False),
            'phone_validated': phone_validation.get('valid', False),
        }

    def _validate_email(self, email, rules):
        """
        Validate email address based on configuration rules.
        """
        messages = []
        
        # Basic syntax check
        if rules.get('syntax_check', True):
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                messages.append(_('Invalid email address format'))
                return {'valid': False, 'messages': messages}
        
        # MX record verification and domain existence
        if rules.get('mx_verification', True):
            domain = email.split('@')[1] if '@' in email else ''
            if domain:
                try:
                    # Check if domain exists using MX or A records
                    import dns.resolver
                    try:
                        # Try MX record first
                        dns.resolver.resolve(domain, 'MX')
                    except:
                        try:
                            # If MX fails, try A record
                            dns.resolver.resolve(domain, 'A')
                        except:
                            messages.append(_('Email domain does not exist or cannot receive emails'))
                            return {'valid': False, 'messages': messages}
                    
                    # Additional verification with verify-email library if available
                    if verify_email:
                        try:
                            if not verify_email(email):
                                messages.append(_('Email address cannot receive emails'))
                                return {'valid': False, 'messages': messages}
                        except Exception as e:
                            _logger.warning(f"verify-email check failed for {email}: {str(e)}")
                            
                except ImportError:
                    # If dns.resolver not available, use basic verification
                    if verify_email:
                        try:
                            if not verify_email(email):
                                messages.append(_('Email domain verification failed'))
                                return {'valid': False, 'messages': messages}
                        except Exception as e:
                            _logger.warning(f"Email verification failed for {email}: {str(e)}")
                except Exception as e:
                    _logger.warning(f"Domain verification failed for {email}: {str(e)}")
                    # Don't block if DNS check fails due to network issues
        
        # Disposable email check
        if rules.get('disposable_check', True) and is_disposable:
            try:
                if is_disposable(email):
                    messages.append(_('Temporary or disposable email addresses are not allowed'))
            except Exception as e:
                _logger.warning(f"Disposable email check failed for {email}: {str(e)}")
        
        # Check for existing registration
        existing_user = request.env['saas.user'].sudo().search([('su_email', '=', email)], limit=1)
        if existing_user:
            messages.append(_('An account with this email address already exists'))
        
        return {
            'valid': len(messages) == 0,
            'messages': messages
        }

    def _validate_phone(self, phone, rules, country_id=None):
        """
        Validate phone number based on configuration rules and selected country.
        """
        messages = []
        formatted_phone = phone
        
        if not rules.get('validation_enabled', True):
            return {'valid': True, 'messages': [], 'formatted': phone}
        
        if phonenumbers:
            try:
                # Get country code from selected country
                country_code = None
                if country_id:
                    country = request.env['res.country'].sudo().browse(int(country_id))
                    if country.exists():
                        country_code = country.code
                
                # Parse phone number with selected country
                parsed = None
                if country_code:
                    try:
                        parsed = phonenumbers.parse(phone, country_code)
                        if phonenumbers.is_valid_number(parsed):
                            formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                        else:
                            parsed = None
                    except:
                        parsed = None
                
                # If country parsing failed, try with country code prefix
                if not parsed:
                    try:
                        parsed = phonenumbers.parse(phone, None)
                        if phonenumbers.is_valid_number(parsed):
                            formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                        else:
                            parsed = None
                    except:
                        parsed = None
                
                # Final validation
                if not parsed or not phonenumbers.is_valid_number(parsed):
                    messages.append(_('Invalid phone number for the selected country. Please check the number format.'))
                    return {'valid': False, 'messages': messages}
                
                # Check if mobile required
                if rules.get('require_mobile', False):
                    number_type = phonenumbers.number_type(parsed)
                    if number_type != phonenumbers.PhoneNumberType.MOBILE:
                        messages.append(_('Only mobile phone numbers are allowed'))
                
            except Exception as e:
                _logger.error(f"Phone validation error: {str(e)}")
                messages.append(_('Phone validation failed. Please enter a valid phone number.'))
        else:
            # Basic validation if phonenumbers library is not available
            if not re.match(r'^\+?[1-9]\d{1,14}$', phone.replace(' ', '').replace('-', '')):
                messages.append(_('Invalid phone number format'))
        
        return {
            'valid': len(messages) == 0,
            'messages': messages,
            'formatted': formatted_phone
        }

    def _create_user_accounts(self, form_data, validation_result):
        """
        Create SaaS user record and portal user account.
        """
        # Prepare user data
        user_data = {
            'first_name': form_data['first_name'],
            'last_name': form_data['last_name'],
            'email': form_data['email'],
            'phone': form_data['phone'],
            'password': form_data['password'],  # This should be encrypted in production
            'email_validated': validation_result['email_validated'],
            'phone_validated': validation_result['phone_validated'],
            'password_strength': validation_result['password_score'],
            'registration_ip': form_data['registration_ip'],
            'user_agent': form_data['user_agent'],
        }
        
        # Create accounts
        saas_user_model = request.env['saas.user'].sudo()
        saas_user, portal_user = saas_user_model.create_saas_user_with_portal(user_data)
        
        _logger.info(f"Successfully created accounts for {form_data['email']}")
        
        return saas_user, portal_user

    def _should_auto_login(self):
        """
        Check if auto-login is enabled in configuration.
        """
        config = request.env['ir.config_parameter'].sudo()
        return config.get_param('j_signup_validation.registration_auto_login', 'True') == 'True'

    def _auto_login_user(self, user):
        """
        Automatically log in the user after registration.
        """
        try:
            request.session.authenticate(request.session.db, user.login, user.login)
            _logger.info(f"Auto-logged in user: {user.login}")
        except Exception as e:
            _logger.error(f"Auto-login failed for user {user.login}: {str(e)}")

    def _redirect_with_error(self, errors):
        """
        Redirect back to signup form with error messages.
        """
        error_message = '; '.join(errors) if isinstance(errors, list) else str(errors)
        return request.redirect(f'/j_signup_validation/signup?error={error_message}')

    def _redirect_with_success(self, message):
        """
        Redirect to signup form with success message.
        """
        return request.redirect(f'/j_signup_validation/signup?success={message}')