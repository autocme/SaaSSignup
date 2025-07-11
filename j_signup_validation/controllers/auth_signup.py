# -*- coding: utf-8 -*-
"""
Authentication and Signup Controllers
Custom controllers for handling user registration with advanced validation.
"""

import json
import logging
import re
import time
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

    @http.route(['/j_signup_validation/signup', '/web/signup'], type='http', auth='public', website=True, sitemap=True, csrf=False)
    def web_auth_signup(self, **kw):
        """
        Display custom signup form.
        """
        try:
            _logger.info("Accessing custom signup form")
            
            # Check if this is a POST request to prevent double processing
            if request.httprequest.method == 'POST':
                return self.web_auth_signup_submit(**kw)
            
            # Get validation rules for frontend
            config_settings = request.env['res.config.settings']
            password_rules = config_settings.get_password_validation_rules()
            email_rules = config_settings.get_email_validation_rules()
            phone_rules = config_settings.get_phone_validation_rules()
            
            # Get countries for phone number selection
            countries = request.env['res.country'].sudo().search([
                ('phone_code', '!=', False)
            ], order='name')
            
            # Get dynamic fields configuration
            dynamic_fields = request.env['signup.configuration'].sudo().get_dynamic_fields()
            
            # Prepare context for template
            values = {
                'password_rules': password_rules,
                'email_rules': email_rules,
                'phone_rules': phone_rules,
                'countries': countries,
                'dynamic_fields': dynamic_fields,
                'error': kw.get('error', ''),
                'success': kw.get('success', ''),
            }
            
            return request.render('j_signup_validation.custom_signup_form', values)
            
        except Exception as e:
            _logger.error(f"Error loading signup form: {str(e)}")
            return request.render('web.login', {'error': _('Unable to load signup form. Please try again.')})

    @http.route(['/j_signup_validation/submit'], type='http', auth='public', methods=['POST'], csrf=False)
    def web_auth_signup_submit(self, **post):
        """
        Process signup form submission with validation.
        """
        try:
            email = post.get('email', '').strip().lower()
            request_id = f"{email}_{int(time.time() * 1000)}"
            _logger.info(f"Processing signup submission for email: {email}, request ID: {request_id}")
            
            # COMPREHENSIVE DUPLICATE PREVENTION - Check for existing users first
            with request.env.cr.savepoint():
                # Check for existing SaaS user
                existing_saas_user = request.env['saas.user'].sudo().search([('su_email', '=', email)], limit=1)
                if existing_saas_user:
                    _logger.warning(f"Duplicate signup attempt for existing SaaS user: {email}, request ID: {request_id}")
                    return self._redirect_with_error(_('An account with this email address already exists. Please try to login instead.'))
                
                # Check for existing portal user
                existing_portal_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                if existing_portal_user:
                    _logger.warning(f"Portal user already exists for email: {email}, request ID: {request_id}")
                    return self._redirect_with_error(_('An account with this email address already exists. Please try to login instead.'))
            
            # Extract form data
            form_data = self._extract_form_data(post)
            
            # Validate all form fields
            validation_result = self._validate_signup_data(form_data)
            
            if not validation_result['valid']:
                _logger.warning(f"Signup validation failed: {validation_result['errors']}")
                return self._redirect_with_error(validation_result['errors'])
            
            # Create SaaS user and portal account (using transaction to ensure atomicity)
            with request.env.cr.savepoint():
                saas_user, portal_user = self._create_user_accounts(form_data, validation_result)
                
                # Verify both users were created successfully
                if not saas_user or not portal_user:
                    raise UserError(_('Failed to create user accounts. Please try again.'))
                
                _logger.info(f"Successfully created SaaS user {saas_user.id} and portal user {portal_user.id}")
            
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
    def validate_phone_ajax(self, phone, country_id=None):
        """
        AJAX endpoint for real-time phone validation.
        """
        try:
            _logger.info(f"Validating phone via AJAX: {phone}, Country ID: {country_id}")
            
            config_settings = request.env['res.config.settings']
            phone_rules = config_settings.get_phone_validation_rules()
            
            # If no country_id provided, try to get it from the form or use default
            if not country_id:
                # Try to get default Saudi Arabia
                default_country = request.env.ref('base.sa', raise_if_not_found=False)
                if default_country:
                    country_id = default_country.id
                    _logger.info(f"AJAX validation: Using default Saudi Arabia country ID: {country_id}")
            
            validation_result = self._validate_phone(phone, phone_rules, country_id)
            
            return {
                'valid': validation_result['valid'],
                'messages': validation_result['messages'],
                'formatted': validation_result.get('formatted', phone),
                'phone_type': validation_result.get('phone_type', 'unknown')
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
        form_data = {
            'first_name': post.get('first_name', '').strip(),
            'last_name': post.get('last_name', '').strip(),
            'company_name': post.get('company_name', '').strip(),
            'email': post.get('email', '').strip().lower(),
            'phone': post.get('phone', '').strip(),
            'phone_country': post.get('phone_country', ''),
            'password': post.get('password', ''),
            'confirm_password': post.get('confirm_password', ''),
            'account_type': post.get('account_type', 'individual').strip(),
            'vat_cr_number': post.get('vat_cr_number', '').strip(),
            'registration_ip': request.httprequest.environ.get('REMOTE_ADDR'),
            'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
        }
        
        # Extract dynamic fields
        dynamic_fields = request.env['signup.configuration'].sudo().get_dynamic_fields()
        form_data['dynamic_fields'] = {}
        
        for field_config in dynamic_fields:
            field_name = field_config['field_name']
            field_value = post.get(field_name, '')
            
            # Handle different field types
            if field_config['field_type'] == 'boolean':
                field_value = bool(field_value)
            elif field_config['field_type'] in ['integer']:
                try:
                    field_value = int(field_value) if field_value else 0
                except ValueError:
                    field_value = 0
            elif field_config['field_type'] == 'float':
                try:
                    field_value = float(field_value) if field_value else 0.0
                except ValueError:
                    field_value = 0.0
            elif field_config['field_type'] == 'binary':
                # Handle file uploads
                field_value = post.get(field_name, None)
            else:
                # Default to string processing
                field_value = str(field_value).strip() if field_value else ''
            
            form_data['dynamic_fields'][field_name] = field_value
        
        return form_data

    def _validate_signup_data(self, form_data):
        """
        Comprehensive validation of signup data.
        """
        errors = []
        email_validation = {'valid': False}
        phone_validation = {'valid': False}
        password_validation = {'valid': False, 'score': 0}
        
        # Basic field validation
        account_type = form_data.get('account_type', 'individual')
        
        # Validate required fields based on account type
        if account_type == 'individual':
            if not form_data['first_name']:
                errors.append(_('First name is required for individual accounts'))
            if not form_data['last_name']:
                errors.append(_('Last name is required for individual accounts'))
        elif account_type == 'company':
            if not form_data['company_name']:
                errors.append(_('Company name is required for company accounts'))
        
        # Common required fields for all account types
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
            
            # Debug logging for phone country issue
            phone_country = form_data.get('phone_country')
            _logger.info(f"Phone validation debug - Phone: {form_data['phone']}, Country: {phone_country}, Type: {type(phone_country)}")
            
            # Only use default Saudi Arabia if NO country is provided at all
            if not phone_country or phone_country == '' or phone_country == 'None':
                default_country = request.env.ref('base.sa', raise_if_not_found=False)
                if default_country:
                    phone_country = default_country.id
                    _logger.info(f"No country provided - using default Saudi Arabia country ID: {phone_country}")
            else:
                _logger.info(f"User selected country ID: {phone_country}")
            
            phone_validation = self._validate_phone(form_data['phone'], phone_rules, phone_country)
            if not phone_validation['valid']:
                errors.extend(phone_validation['messages'])
            else:
                # Store phone type for later use in portal user creation
                form_data['phone_type'] = phone_validation.get('phone_type', 'unknown')
                form_data['formatted_phone'] = phone_validation.get('formatted', form_data['phone'])
        
        # Password validation
        if form_data['password']:
            config_settings = request.env['res.config.settings']
            password_validation = config_settings.validate_password_strength(form_data['password'])
            if not password_validation['valid']:
                errors.extend(password_validation['messages'])
        
        # VAT/CR validation for company accounts
        if form_data.get('account_type') == 'company':
            vat_cr = form_data.get('vat_cr_number', '').strip()
            if not vat_cr:
                errors.append(_('VAT/CR number is required for company accounts'))
            elif len(vat_cr) < 10 or not re.match(r'^[A-Za-z0-9]+$', vat_cr):
                errors.append(_('VAT/CR number must be at least 10 alphanumeric characters'))
        
        # Dynamic fields validation
        self._validate_dynamic_fields(form_data, errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'password_score': password_validation.get('score', 0),
            'email_validated': email_validation.get('valid', False),
            'phone_validated': phone_validation.get('valid', False),
        }

    def _check_disposable_email(self, email):
        """
        Check if email is disposable using configured method (library or API).
        """
        messages = []
        
        # Get temp mail detection configuration
        config = request.env['ir.config_parameter'].sudo()
        detection_method = config.get_param('j_signup_validation.temp_mail_detection_method', 'library')
        
        try:
            if detection_method == 'api':
                # Use TempMailDetector API
                api_key = config.get_param('j_signup_validation.temp_mail_api_key', '')
                if not api_key:
                    _logger.warning("TempMailDetector API key not configured, falling back to library method")
                    return self._check_disposable_email_library(email)
                
                return self._check_disposable_email_api(email, api_key)
            else:
                # Use library method (default)
                return self._check_disposable_email_library(email)
                
        except Exception as e:
            _logger.warning(f"Disposable email check failed for {email}: {str(e)}")
            # If both methods fail, allow the email (don't block legitimate users)
            return {'valid': True, 'messages': []}

    def _check_disposable_email_library(self, email):
        """
        Check disposable email using disposable_email_validator library.
        """
        messages = []
        
        try:
            if is_disposable_email(email):
                messages.append(_('Temporary or disposable email addresses are not allowed'))
                return {'valid': False, 'messages': messages}
        except Exception as e:
            _logger.warning(f"Library disposable email check failed for {email}: {str(e)}")
        
        return {'valid': True, 'messages': messages}

    def _check_disposable_email_api(self, email, api_key):
        """
        Check disposable email using TempMailDetector API.
        """
        import json
        import requests
        
        messages = []
        domain = email.split('@')[1].lower()
        
        try:
            API_URL = "https://api.tempmaildetector.com/check"
            CONTENT_TYPE = "application/json"
            request_body = json.dumps({"domain": domain})
            headers = {
                "Content-Type": CONTENT_TYPE,
                "Authorization": api_key,
            }

            response = requests.post(API_URL, data=request_body, headers=headers, timeout=10)

            if response.status_code != 200:
                _logger.warning(f"TempMailDetector API returned {response.status_code}: {response.text}")
                # Fall back to library method on API failure
                return self._check_disposable_email_library(email)

            response_data = response.json()
            _logger.info(f'TempMailDetector response for {domain}: {response_data}')
            
            # Check if domain is in block list or has suspicious characteristics
            meta = response_data.get('meta', {})
            score = response_data.get('score', 0)
            
            # Block if domain is in block list or has high suspicion score
            if meta.get('block_list', False) or score >= 90:
                messages.append(_('Temporary or disposable email addresses are not allowed'))
                return {'valid': False, 'messages': messages}
                
        except requests.exceptions.Timeout:
            _logger.warning(f"TempMailDetector API timeout for {domain}")
            # Fall back to library method on timeout
            return self._check_disposable_email_library(email)
        except Exception as e:
            _logger.warning(f"TempMailDetector API check failed for {domain}: {str(e)}")
            # Fall back to library method on API error
            return self._check_disposable_email_library(email)
        
        return {'valid': True, 'messages': messages}

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
        if rules.get('disposable_check', True):
            temp_mail_result = self._check_disposable_email(email)
            if not temp_mail_result['valid']:
                messages.extend(temp_mail_result['messages'])
                return {'valid': False, 'messages': messages}
        
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
        Enforces strict country matching and determines phone type for proper field assignment.
        """
        messages = []
        formatted_phone = phone
        phone_type = None
        
        if not rules.get('validation_enabled', True):
            return {'valid': True, 'messages': [], 'formatted': phone, 'phone_type': 'unknown'}
        
        if not phone.strip():
            messages.append(_('Phone number is required'))
            return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
        
        if phonenumbers:
            try:
                # Get country info from selected country - REQUIRED for strict validation
                country = None
                country_code = None
                
                if country_id:
                    try:
                        country = request.env['res.country'].sudo().browse(int(country_id))
                        if country.exists():
                            country_code = country.code  # e.g., 'SA', 'JO'
                            _logger.info(f"Validating phone for country: {country.name} ({country_code})")
                        else:
                            _logger.error(f"Country with ID {country_id} does not exist")
                    except Exception as e:
                        _logger.error(f"Error accessing country with ID {country_id}: {str(e)}")
                
                # Country is REQUIRED for strict validation
                if not country or not country_code:
                    _logger.error(f"Country selection required for phone validation - country: {country}, country_id: {country_id}")
                    messages.append(_('Please select a country for phone number validation'))
                    return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
                
                # STEP 1: Parse phone number with selected country region
                parsed = None
                try:
                    # Parse with country region code (e.g., 'SA' for Saudi Arabia)
                    parsed = phonenumbers.parse(phone, country_code)
                    _logger.info(f"Parsed phone number '{phone}' with country region '{country_code}'")
                except phonenumbers.NumberParseException as e:
                    _logger.error(f"Failed to parse phone number '{phone}' with country '{country_code}': {str(e)}")
                    messages.append(_('Invalid phone number format for %s') % country.name)
                    return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
                
                # STEP 2: Validate the parsed number
                if not phonenumbers.is_valid_number(parsed):
                    _logger.error(f"Phone number '{phone}' is not valid")
                    messages.append(_('Invalid phone number'))
                    return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
                
                # STEP 3: CRITICAL - Enforce strict country matching
                number_region = phonenumbers.region_code_for_number(parsed)
                if number_region != country_code:
                    _logger.warning(f"COUNTRY MISMATCH: Phone number region '{number_region}' does not match selected country '{country_code}'")
                    messages.append(_('Phone number must belong to %s. The number you entered belongs to a different country.') % country.name)
                    return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
                
                # STEP 4: Determine phone number type using phonenumbers library
                from phonenumbers import NumberParseException, number_type, PhoneNumberType
                
                num_type = number_type(parsed)
                if num_type == PhoneNumberType.MOBILE:
                    phone_type = 'mobile'
                    _logger.info(f"Phone number identified as MOBILE: {phone}")
                elif num_type == PhoneNumberType.FIXED_LINE:
                    phone_type = 'fixed_line'
                    _logger.info(f"Phone number identified as FIXED_LINE: {phone}")
                elif num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE:
                    phone_type = 'fixed_line_or_mobile'
                    _logger.info(f"Phone number identified as FIXED_LINE_OR_MOBILE: {phone}")
                else:
                    _logger.warning(f"Phone number type not recognized: {num_type}")
                    messages.append(_('Phone number type not supported'))
                    return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
                
                # STEP 5: Check mobile requirement if configured
                if rules.get('require_mobile', False):
                    if phone_type not in ['mobile', 'fixed_line_or_mobile']:
                        messages.append(_('Only mobile phone numbers are allowed'))
                        return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
                
                # STEP 6: Format for storage (international format)
                formatted_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                
                _logger.info(f"Phone validation SUCCESS: {formatted_phone} (Type: {phone_type}, Country: {country_code})")
                
            except Exception as e:
                _logger.error(f"Phone validation error: {str(e)}")
                messages.append(_('Phone validation failed. Please enter a valid phone number.'))
                return {'valid': False, 'messages': messages, 'formatted': formatted_phone, 'phone_type': phone_type}
        else:
            # Basic validation if phonenumbers library is not available
            if not re.match(r'^\+?[1-9]\d{1,14}$', phone.replace(' ', '').replace('-', '')):
                messages.append(_('Invalid phone number format'))
            else:
                phone_type = 'unknown'  # Can't determine type without phonenumbers library
        
        return {
            'valid': len(messages) == 0,
            'messages': messages,
            'formatted': formatted_phone,
            'phone_type': phone_type
        }

    def _validate_dynamic_fields(self, form_data, errors):
        """
        Validate required dynamic fields.
        """
        try:
            # Get dynamic fields configuration
            dynamic_fields = request.env['signup.configuration'].sudo().get_dynamic_fields()
            
            for field_config in dynamic_fields:
                field_name = field_config['field_name']
                field_label = field_config['field_label']
                is_required = field_config['required']
                field_type = field_config['field_type']
                
                # Check if field is required
                if is_required:
                    field_value = form_data.get('dynamic_fields', {}).get(field_name)
                    
                    # Validate based on field type
                    if field_type == 'boolean':
                        # Boolean fields are always valid (True or False)
                        continue
                    elif field_type == 'binary':
                        # Check if file was uploaded
                        if not field_value:
                            errors.append(_('%s is required') % field_label)
                    else:
                        # String, text, integer, float, date, datetime fields
                        if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                            errors.append(_('%s is required') % field_label)
                        
                        # Additional validation for numeric fields
                        if field_type in ['integer', 'float'] and field_value == 0:
                            # Check if 0 is a valid value or if it means empty
                            raw_value = request.httprequest.form.get(field_name, '').strip()
                            if not raw_value:
                                errors.append(_('%s is required') % field_label)
                                
        except Exception as e:
            _logger.error(f"Dynamic fields validation error: {str(e)}")
            # Don't add error here as it might be configuration issue

    def _create_user_accounts(self, form_data, validation_result):
        """
        Create SaaS user record and portal user account.
        """
        try:
            email = form_data['email']
            
            # Double-check for existing users in the same transaction
            existing_saas = request.env['saas.user'].sudo().search([('su_email', '=', email)], limit=1)
            if existing_saas:
                raise ValidationError(_('A SaaS user with this email already exists.'))
                
            existing_portal = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing_portal:
                raise ValidationError(_('A portal user with this email already exists.'))
            
            # Prepare SaaS user data
            saas_user_vals = {
                'su_first_name': form_data['first_name'],
                'su_last_name': form_data['last_name'],
                'su_company_name': form_data['company_name'],
                'su_email': email,
                'su_phone': form_data['phone'],
                'su_password': form_data['password'],
                'su_account_type': form_data.get('account_type', 'individual'),
                'su_vat_cr_number': form_data.get('vat_cr_number', ''),
                'su_email_validated': validation_result['email_validated'],
                'su_phone_validated': validation_result['phone_validated'],
                'su_password_strength': validation_result['password_score'],
                'su_registration_ip': form_data['registration_ip'],
                'su_user_agent': form_data['user_agent'],
            }
            
            # Handle phone country - convert string ID to integer
            phone_country = form_data.get('phone_country')
            if phone_country:
                try:
                    phone_country_id = int(phone_country)
                    saas_user_vals['su_phone_country_id'] = phone_country_id
                    _logger.info(f"Setting phone country ID to {phone_country_id} for SaaS user creation")
                except (ValueError, TypeError) as e:
                    _logger.warning(f"Invalid phone country value '{phone_country}': {str(e)}")
                    # Use default country (Saudi Arabia) if conversion fails
                    default_country = request.env.ref('base.sa', raise_if_not_found=False)
                    if default_country:
                        saas_user_vals['su_phone_country_id'] = default_country.id
                        _logger.info(f"Using default country {default_country.id} (Saudi Arabia)")
            else:
                # Use default country if no country provided
                default_country = request.env.ref('base.sa', raise_if_not_found=False)
                if default_country:
                    saas_user_vals['su_phone_country_id'] = default_country.id
                    _logger.info(f"Using default country {default_country.id} (Saudi Arabia) - no country provided")
            
            # Create SaaS user with dynamic fields and phone type in context
            # The create method will automatically create the portal user
            saas_user_model = request.env['saas.user'].sudo()
            dynamic_fields = form_data.get('dynamic_fields', {})
            phone_type = form_data.get('phone_type', 'unknown')
            formatted_phone = form_data.get('formatted_phone', form_data.get('phone', ''))
            
            # Create with explicit context to prevent duplicate creation
            saas_user = saas_user_model.with_context(
                dynamic_fields=dynamic_fields,
                phone_type=phone_type,
                formatted_phone=formatted_phone,
                from_signup_form=True  # Flag to indicate this is from signup form
            ).create(saas_user_vals)
            
            # Verify portal user was created
            if not saas_user.su_portal_user_id:
                raise UserError(_('Failed to create portal user account.'))
            
            _logger.info(f"Successfully created SaaS user {saas_user.id} and portal user {saas_user.su_portal_user_id.id} for {email}")
            
            return saas_user, saas_user.su_portal_user_id
            
        except Exception as e:
            _logger.error(f"Error creating user accounts for {form_data.get('email', 'unknown')}: {str(e)}")
            raise

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