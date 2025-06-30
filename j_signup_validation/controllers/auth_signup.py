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
except ImportError:
    verify_email = None

try:
    from disposable_email_validator import is_disposable_email
except ImportError:
    is_disposable_email = None

try:
    import phonenumbers
    from phonenumbers import NumberParseException
except ImportError:
    phonenumbers = None

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    dns = None

_logger = logging.getLogger(__name__)


class CustomAuthSignup(http.Controller):
    """
    Custom authentication controller for handling signup with validation.
    """

    @http.route('/j_signup_validation/test', type='http', auth='public', csrf=False)
    def test_route(self, **kw):
        """Test route to verify controller is working."""
        return "Custom signup controller is working!"

    @http.route(['/web/signup', '/j_signup_validation/signup'], type='http', auth='public', csrf=False)
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
            
            return request.render('j_signup_validation.signup_custom', values)
            
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
                domain_valid = False
                
                # First try DNS resolution
                if DNS_AVAILABLE:
                    try:
                        # Try MX record first
                        mx_records = dns.resolver.resolve(domain, 'MX')
                        # Check if MX records point to valid mail servers
                        valid_mx = False
                        for mx in mx_records:
                            mx_host = str(mx.exchange).rstrip('.')
                            # Reject invalid/parked domain indicators
                            if mx_host not in ['0.0.0.0', 'localhost', '127.0.0.1', ''] and not mx_host.startswith('0.'):
                                valid_mx = True
                                break
                        
                        if valid_mx:
                            domain_valid = True
                        else:
                            messages.append(_('Email domain does not accept emails'))
                            return {'valid': False, 'messages': messages}
                            
                    except dns.resolver.NXDOMAIN:
                        messages.append(_('Email domain does not exist'))
                        return {'valid': False, 'messages': messages}
                    except dns.resolver.NoAnswer:
                        try:
                            # If MX fails, try A record
                            dns.resolver.resolve(domain, 'A')
                            # Domain exists but no mail service - still reject for email registration
                            messages.append(_('Email domain does not support email delivery'))
                            return {'valid': False, 'messages': messages}
                        except dns.resolver.NXDOMAIN:
                            messages.append(_('Email domain does not exist'))
                            return {'valid': False, 'messages': messages}
                        except:
                            pass
                    except Exception as e:
                        _logger.warning(f"DNS check failed for {domain}: {str(e)}")
                else:
                    _logger.warning("dnspython not available for DNS verification")
                
                # If DNS checks failed but we have verify-email, try basic domain check
                if not domain_valid:
                    # Basic domain structure validation as fallback
                    domain_parts = domain.split('.')
                    if len(domain_parts) < 2 or len(domain_parts[-1]) < 2:
                        messages.append(_('Email domain appears to be invalid'))
                        return {'valid': False, 'messages': messages}
                    
                    # For common parked/invalid domains, reject them
                    parked_domains = ['foo.com', 'bar.com', 'test.com', 'example.com', 'temp.com']
                    if domain.lower() in parked_domains:
                        messages.append(_('Email domain does not accept emails'))
                        return {'valid': False, 'messages': messages}
        
        # Disposable email check
        if rules.get('disposable_check', True) and is_disposable_email:
            try:
                if is_disposable_email(email):
                    messages.append(_('Temporary or disposable email addresses are not allowed'))
                    return {'valid': False, 'messages': messages}
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
                # Get country info from selected country
                country = None
                country_code = None
                current_phone_code = None
                
                if country_id:
                    try:
                        country = request.env['res.country'].sudo().browse(int(country_id))
                        if country.exists():
                            country_code = country.code  # e.g., 'JO'
                            # Try to get phone_code from country (may not exist in standard Odoo)
                            current_phone_code = getattr(country, 'phone_code', None)
                            _logger.info(f"Country found: {country.name}, code: {country_code}, phone_code: {current_phone_code}")
                        else:
                            _logger.error(f"Country with ID {country_id} does not exist")
                    except Exception as e:
                        _logger.error(f"Error accessing country with ID {country_id}: {str(e)}")
                        country = None
                        country_code = None
                
                # If no country provided, try to validate phone as international number
                if not country or not country_code:
                    if not country_id:
                        # No country provided, try parsing as international number
                        try:
                            parsed = phonenumbers.parse(phone, None)
                            if phonenumbers.is_valid_number(parsed):
                                formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                                _logger.info(f"Phone validated as international number: {formatted_phone}")
                                return {
                                    'valid': True,
                                    'messages': [],
                                    'formatted': formatted_phone
                                }
                        except:
                            pass
                    
                    _logger.error(f"Validation failed - country: {bool(country)}, country_code: {country_code}")
                    messages.append(_('Please select a valid country for phone number validation.'))
                    return {'valid': False, 'messages': messages}
                
                # Handle phone numbers that may already contain country codes
                # User input examples: "+962 777771111", "962777771111", "0777771111", "777771111"
                
                parsed = None
                international_number = phone  # Default to original input
                
                # Try to parse the phone number as-is first
                try:
                    temp_parsed = phonenumbers.parse(phone, None)
                    if phonenumbers.is_valid_number(temp_parsed):
                        # Check if it matches the selected country
                        number_region = phonenumbers.region_code_for_number(temp_parsed)
                        if number_region == country_code:
                            parsed = temp_parsed
                            international_number = phone
                            _logger.info(f"Phone already valid with country code: {phone}")
                except:
                    pass
                
                # If parsing failed or wrong country, try with country region code
                if not parsed:
                    # Try parsing with the country region code (like 'JO' for Jordan)
                    try:
                        temp_parsed = phonenumbers.parse(phone, country_code)
                        if phonenumbers.is_valid_number(temp_parsed):
                            parsed = temp_parsed
                            international_number = phonenumbers.format_number(temp_parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                            _logger.info(f"Phone parsed with country region: {international_number}")
                    except:
                        pass
                
                # If still not parsed, try basic validation
                if not parsed:
                    _logger.error(f"Unable to parse phone number: {phone} for country: {country_code}")
                    messages.append(_('Invalid phone number format for the selected country.'))
                    return {'valid': False, 'messages': messages}
                
                # Final validation of the parsed number
                if not parsed or not phonenumbers.is_valid_number(parsed):
                    messages.append(_('Invalid phone number for the selected country.'))
                    return {'valid': False, 'messages': messages}
                
                # Verify the number belongs to the selected country
                number_region = phonenumbers.region_code_for_number(parsed)
                if number_region != country_code:
                    messages.append(_(f'Phone number does not match the selected country ({country.name}).'))
                    return {'valid': False, 'messages': messages}
                
                # Format for storage (international format)
                formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                
                # Check if mobile required
                if rules.get('require_mobile', False):
                    number_type = phonenumbers.number_type(parsed)
                    if number_type != phonenumbers.PhoneNumberType.MOBILE:
                        messages.append(_('Only mobile phone numbers are allowed.'))
                        return {'valid': False, 'messages': messages}
                
                _logger.info(f"Phone validation SUCCESS: {formatted_phone}")
                
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
            'phone_country': form_data.get('phone_country'),
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