# -*- coding: utf-8 -*-
"""
SaaS User Model
Custom model to store user registration information for future reference.
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class SaasUser(models.Model):
    """
    SaaS User model to store custom user registration data.
    This model maintains user information separately from res.users
    for future reference and additional password validation.
    """
    _name = 'saas.user'
    _description = 'SaaS User Registration Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'su_complete_name'

    # Basic Information Fields
    su_first_name = fields.Char(
        'First Name',
        tracking=True,
        help='User\'s first name as provided during registration - required for individual accounts'
    )
    
    su_last_name = fields.Char(
        'Last Name',
        tracking=True,
        help='User\'s last name as provided during registration - required for individual accounts'
    )
    
    su_company_name = fields.Char(
        'Company Name',
        tracking=True,
        help='Company name - required for company accounts'
    )
    
    su_complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name',
        store=True,
        help='Full name computed from first and last name'
    )
    
    su_email = fields.Char(
        'Email Address',
        required=True,
        tracking=True,
        help='User\'s email address used for registration and login'
    )
    
    su_phone_country_id = fields.Many2one(
        'res.country',
        'Phone Country',
        default=lambda self: self.env.ref('base.sa'),  # Saudi Arabia as default
        required=True,
        tracking=True,
        help='Country for phone number validation and formatting'
    )
    
    su_phone = fields.Char(
        'Phone Number',
        required=True,
        tracking=True,
        help='User\'s phone number with international format validation'
    )

    su_account_type = fields.Selection([
        ('individual', 'Individual'),
        ('company', 'Company')
    ], 'Account Type', 
        required=True, 
        default='individual',
        tracking=True,
        help='Type of account registration - Individual or Company'
    )

    su_vat_cr_number = fields.Char(
        'VAT/CR Number',
        tracking=True,
        help='VAT or Commercial Registration number for company accounts'
    )
    
    su_password = fields.Char(
        'Password',
        required=True,
        help='Encrypted password for additional validation purposes'
    )
    
    # Validation Status Fields
    su_email_validated = fields.Boolean(
        'Email Validated',
        default=False,
        tracking=True,
        help='Indicates if email passed all validation checks'
    )
    
    su_phone_validated = fields.Boolean(
        'Phone Validated',
        default=False,
        tracking=True,
        help='Indicates if phone number passed validation checks'
    )
    
    su_password_strength = fields.Integer(
        'Password Strength Score',
        default=0,
        tracking=True,
        help='Password strength score from 0-100 based on validation rules'
    )
    
    # Registration Details
    su_registration_ip = fields.Char(
        'Registration IP',
        tracking=True,
        help='IP address from which the user registered'
    )
    
    su_registration_date = fields.Datetime(
        'Registration Date',
        default=fields.Datetime.now,
        tracking=True,
        help='Date and time when user completed registration'
    )
    
    su_user_agent = fields.Text(
        'User Agent',
        help='Browser user agent string during registration'
    )
    
    # Related Portal User
    su_portal_user_id = fields.Many2one(
        'res.users',
        'Portal User',
        tracking=True,
        help='Related portal user account created during registration'
    )
    
    su_active = fields.Boolean(
        'Active',
        default=True,
        tracking=True,
        help='Indicates if the SaaS user record is active'
    )
    
    # SQL constraints for database-level duplicate prevention
    _sql_constraints = [
        ('unique_email', 'UNIQUE(su_email)', 'An account with this email address already exists.'),
    ]

    @api.depends('su_first_name', 'su_last_name', 'su_company_name', 'su_account_type')
    def _compute_complete_name(self):
        """
        Compute the complete name from first and last name for individuals or company name for companies.
        """
        for record in self:
            try:
                if record.su_account_type == 'company' and record.su_company_name:
                    # For company accounts, use company name
                    record.su_complete_name = record.su_company_name
                elif record.su_account_type == 'individual':
                    # For individual accounts, use first and last name
                    if record.su_first_name and record.su_last_name:
                        record.su_complete_name = f"{record.su_first_name} {record.su_last_name}"
                    elif record.su_first_name:
                        record.su_complete_name = record.su_first_name
                    elif record.su_last_name:
                        record.su_complete_name = record.su_last_name
                    else:
                        record.su_complete_name = 'Unnamed User'
                else:
                    record.su_complete_name = 'Unnamed User'
            except Exception as e:
                _logger.error(f"Error computing complete name for SaaS user {record.id}: {str(e)}")
                record.su_complete_name = f"User {record.id}"
        
        _logger.info(f"Computed complete names for {len(self)} SaaS user records")

    @api.constrains('su_email')
    def _check_email_unique(self):
        """
        Ensure email uniqueness across SaaS users.
        """
        for record in self:
            if record.su_email:
                existing = self.search([
                    ('su_email', '=', record.su_email),
                    ('id', '!=', record.id)
                ])
                if existing:
                    _logger.warning(f"Duplicate email registration attempt: {record.su_email}")
                    raise ValidationError(
                        _("An account with this email address already exists. "
                          "Please use a different email or try to login.")
                    )

    @api.constrains('su_account_type', 'su_first_name', 'su_last_name', 'su_company_name')
    def _check_account_type_fields(self):
        """
        Validate required fields based on account type.
        For individual accounts: first_name and last_name are required
        For company accounts: company_name is required
        """
        for record in self:
            if record.su_account_type == 'individual':
                if not record.su_first_name or not record.su_last_name:
                    raise ValidationError(
                        _("First Name and Last Name are required for individual accounts.")
                    )
            elif record.su_account_type == 'company':
                if not record.su_company_name:
                    raise ValidationError(
                        _("Company Name is required for company accounts.")
                    )

    @api.model
    def create(self, vals):
        """
        Override create method to automatically create portal user when SaaS user is created.
        """
        # Create the SaaS user record first
        saas_user = super(SaasUser, self).create(vals)
        
        try:
            # Check if portal user should be created (skip if already linked)
            if not saas_user.su_portal_user_id and saas_user.su_email and saas_user.su_password:
                
                # Check if portal user already exists to prevent duplicates
                existing_portal_user = self.env['res.users'].sudo().search([
                    ('login', '=', saas_user.su_email)
                ], limit=1)
                
                if existing_portal_user:
                    _logger.info(f"Portal user already exists for email {saas_user.su_email}, linking to SaaS user {saas_user.id}")
                    # Link existing portal user to SaaS user
                    saas_user.write({'su_portal_user_id': existing_portal_user.id})
                    return saas_user
                
                _logger.info(f"Auto-creating portal user for SaaS user {saas_user.id} with email: {saas_user.su_email}")
                
                # Prepare portal user data
                portal_user_vals = {
                    'name': saas_user.su_complete_name,
                    'login': saas_user.su_email,
                    'email': saas_user.su_email,
                    'password': saas_user.su_password,
                    'is_company': True if saas_user.su_account_type == 'company' else False,
                    'vat': saas_user.su_vat_cr_number if saas_user.su_account_type == 'company' and saas_user.su_vat_cr_number else False,
                }
                
                # Set country_id only if we have a valid country
                if saas_user.su_phone_country_id and saas_user.su_phone_country_id.id:
                    portal_user_vals['country_id'] = saas_user.su_phone_country_id.id
                    _logger.info(f"Setting country_id to {saas_user.su_phone_country_id.id} ({saas_user.su_phone_country_id.name}) for portal user")
                
                # Handle phone field assignment based on phone type
                phone_type = self.env.context.get('phone_type', 'unknown')
                formatted_phone = self.env.context.get('formatted_phone', saas_user.su_phone)
                
                _logger.info(f"Portal user phone assignment - Type: {phone_type}, Phone: {formatted_phone}")
                
                if phone_type == 'mobile':
                    # Mobile number goes to mobile field
                    portal_user_vals['mobile'] = formatted_phone
                    _logger.info(f"Assigned mobile number: {formatted_phone}")
                elif phone_type == 'fixed_line':
                    # Fixed line number goes to phone field
                    portal_user_vals['phone'] = formatted_phone
                    _logger.info(f"Assigned fixed line number: {formatted_phone}")
                elif phone_type == 'fixed_line_or_mobile':
                    # Could be either, assign to both for compatibility
                    portal_user_vals['mobile'] = formatted_phone
                    portal_user_vals['phone'] = formatted_phone
                    _logger.info(f"Assigned to both mobile and phone fields: {formatted_phone}")
                else:
                    # Unknown type, assign to mobile by default (most common)
                    portal_user_vals['mobile'] = formatted_phone
                    _logger.info(f"Unknown phone type, assigned to mobile field: {formatted_phone}")

                # Check if any dynamic fields were passed in context
                dynamic_fields = self.env.context.get('dynamic_fields', {})
                for field_name, field_value in dynamic_fields.items():
                    # Only add if the field exists in res.users model
                    if hasattr(self.env['res.users'], field_name):
                        portal_user_vals[field_name] = field_value
                
                # Create portal user using normal create method
                portal_group = self.env.ref('base.group_portal')
                portal_user_vals['groups_id'] = [(6, 0, [portal_group.id])]
                portal_user_vals['active'] = True
                # Set bidirectional relation - portal user points to SaaS user
                portal_user_vals['saas_user_id'] = saas_user.id
                
                # Use savepoint to ensure atomicity
                with self.env.cr.savepoint():
                    portal_user = self.env['res.users'].sudo().create(portal_user_vals)
                    
                    # Link the portal user to SaaS user (completing bidirectional relation)
                    saas_user.write({'su_portal_user_id': portal_user.id})
                    
                    _logger.info(f"Successfully auto-created portal user {portal_user.id} for SaaS user {saas_user.id}")
                
        except Exception as e:
            _logger.error(f"Error auto-creating portal user for SaaS user {saas_user.id}: {str(e)}")
            # Don't raise error here to prevent SaaS user creation failure
            # Portal user can be created manually later if needed
            
        return saas_user

    def action_create_portal_user(self):
        """
        Manually create portal user for existing SaaS user records.
        This is useful for SaaS users created before the automatic portal user creation.
        """
        self.ensure_one()
        
        if self.su_portal_user_id:
            raise UserError(_('This SaaS user already has a linked portal user.'))
        
        if not self.su_email or not self.su_password:
            raise UserError(_('Email and password are required to create a portal user.'))
        
        try:
            _logger.info(f"Manually creating portal user for SaaS user {self.id} with email: {self.su_email}")
            
            # Prepare portal user data
            portal_user_vals = {
                'name': self.su_complete_name,
                'login': self.su_email,
                'email': self.su_email,
                'password': self.su_password,
                'is_company': True if self.su_account_type == 'company' else False,
                'vat': self.su_vat_cr_number if self.su_account_type == 'company' and self.su_vat_cr_number else False,
            }
            
            # Set country_id only if we have a valid country
            if self.su_phone_country_id and self.su_phone_country_id.id:
                portal_user_vals['country_id'] = self.su_phone_country_id.id
                _logger.info(f"Setting country_id to {self.su_phone_country_id.id} ({self.su_phone_country_id.name}) for portal user")
            
            # For manual creation, we need to determine phone type using phonenumbers library
            phone_type = 'unknown'
            if self.su_phone and self.su_phone_country_id:
                try:
                    import phonenumbers
                    from phonenumbers import NumberParseException, number_type, PhoneNumberType
                    
                    # Parse phone number to determine type
                    parsed = phonenumbers.parse(self.su_phone, self.su_phone_country_id.code)
                    if phonenumbers.is_valid_number(parsed):
                        num_type = number_type(parsed)
                        if num_type == PhoneNumberType.MOBILE:
                            phone_type = 'mobile'
                        elif num_type == PhoneNumberType.FIXED_LINE:
                            phone_type = 'fixed_line'
                        elif num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE:
                            phone_type = 'fixed_line_or_mobile'
                        
                        _logger.info(f"Manual portal user creation - Phone type determined: {phone_type}")
                except Exception as e:
                    _logger.warning(f"Could not determine phone type for manual creation: {str(e)}")
                    phone_type = 'unknown'
            
            # Handle phone field assignment based on phone type
            _logger.info(f"Manual portal user phone assignment - Type: {phone_type}, Phone: {self.su_phone}")
            
            if phone_type == 'mobile':
                # Mobile number goes to mobile field
                portal_user_vals['mobile'] = self.su_phone
                _logger.info(f"Assigned mobile number: {self.su_phone}")
            elif phone_type == 'fixed_line':
                # Fixed line number goes to phone field
                portal_user_vals['phone'] = self.su_phone
                _logger.info(f"Assigned fixed line number: {self.su_phone}")
            elif phone_type == 'fixed_line_or_mobile':
                # Could be either, assign to both for compatibility
                portal_user_vals['mobile'] = self.su_phone
                portal_user_vals['phone'] = self.su_phone
                _logger.info(f"Assigned to both mobile and phone fields: {self.su_phone}")
            else:
                # Unknown type, assign to mobile by default (most common)
                portal_user_vals['mobile'] = self.su_phone
                _logger.info(f"Unknown phone type, assigned to mobile field: {self.su_phone}")
            
            # Create portal user using normal create method
            portal_group = self.env.ref('base.group_portal')
            portal_user_vals['groups_id'] = [(6, 0, [portal_group.id])]
            portal_user_vals['active'] = True
            # Set bidirectional relation - portal user points to SaaS user
            portal_user_vals['saas_user_id'] = self.id
            
            portal_user = self.env['res.users'].sudo().create(portal_user_vals)
            
            # Link the portal user to SaaS user (completing bidirectional relation)
            self.write({'su_portal_user_id': portal_user.id})
            
            _logger.info(f"Successfully created portal user {portal_user.id} for SaaS user {self.id}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Portal user created successfully.'),
                    'type': 'success',
                },
            }
            
        except Exception as e:
            _logger.error(f"Error creating portal user for SaaS user {self.id}: {str(e)}")
            raise UserError(_("Failed to create portal user. Please check the logs for details."))

    def write(self, vals):
        """
        Override write method to sync changes to linked portal user.
        """
        result = super(SaasUser, self).write(vals)
        
        # Sync data to portal user if any relevant fields changed
        sync_fields = ['su_first_name', 'su_last_name', 'su_company_name', 'su_email', 'su_phone', 'su_phone_country_id', 'su_account_type', 'su_vat_cr_number']
        
        if any(field in vals for field in sync_fields):
            for record in self:
                if record.su_portal_user_id:
                    record._sync_to_portal_user()
        
        return result

    def _sync_to_portal_user(self):
        """
        Sync SaaS User data to linked Portal User.
        Only syncs from SaaS User → Portal User (one-way sync).
        """
        self.ensure_one()
        
        if not self.su_portal_user_id:
            _logger.warning(f"No portal user linked to SaaS user {self.id}, skipping sync")
            return
        
        try:
            _logger.info(f"Syncing SaaS user {self.id} data to portal user {self.su_portal_user_id.id}")
            
            # Prepare sync values
            sync_vals = {
                'name': self.su_complete_name,
                'email': self.su_email,
                'login': self.su_email,
                'is_company': True if self.su_account_type == 'company' else False,
                'vat': self.su_vat_cr_number if self.su_account_type == 'company' and self.su_vat_cr_number else False,
            }
            
            # Set country_id if available
            if self.su_phone_country_id:
                sync_vals['country_id'] = self.su_phone_country_id.id
            
            # Handle phone field sync based on phone type
            if self.su_phone:
                phone_type = 'unknown'
                if self.su_phone_country_id:
                    try:
                        import phonenumbers
                        from phonenumbers import NumberParseException, number_type, PhoneNumberType
                        
                        # Parse phone number to determine type
                        parsed = phonenumbers.parse(self.su_phone, self.su_phone_country_id.code)
                        if phonenumbers.is_valid_number(parsed):
                            num_type = number_type(parsed)
                            if num_type == PhoneNumberType.MOBILE:
                                phone_type = 'mobile'
                            elif num_type == PhoneNumberType.FIXED_LINE:
                                phone_type = 'fixed_line'
                            elif num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE:
                                phone_type = 'fixed_line_or_mobile'
                    except Exception as e:
                        _logger.warning(f"Could not determine phone type for sync: {str(e)}")
                
                # Clear existing phone fields first
                sync_vals['mobile'] = False
                sync_vals['phone'] = False
                
                # Set phone fields based on type
                if phone_type == 'mobile':
                    sync_vals['mobile'] = self.su_phone
                elif phone_type == 'fixed_line':
                    sync_vals['phone'] = self.su_phone
                elif phone_type == 'fixed_line_or_mobile':
                    sync_vals['mobile'] = self.su_phone
                    sync_vals['phone'] = self.su_phone
                else:
                    # Unknown type, assign to mobile by default
                    sync_vals['mobile'] = self.su_phone
            
            # Update portal user
            self.su_portal_user_id.sudo().write(sync_vals)
            
            _logger.info(f"Successfully synced SaaS user {self.id} to portal user {self.su_portal_user_id.id}")
            
        except Exception as e:
            _logger.error(f"Error syncing SaaS user {self.id} to portal user: {str(e)}")
            # Don't raise error to prevent SaaS user update failures

    def get_user_stats(self):
        """
        Get statistics for the current user record.
        
        Returns:
            dict: User statistics and validation status
        """
        self.ensure_one()
        return {
            'registration_date': self.su_registration_date,
            'email_validated': self.su_email_validated,
            'phone_validated': self.su_phone_validated,
            'password_strength': self.su_password_strength,
            'portal_user_active': self.su_portal_user_id.active if self.su_portal_user_id else False,
        }

    def action_view_portal_user(self):
        """
        Open the related portal user record.
        
        Returns:
            dict: Action to open portal user form view
        """
        self.ensure_one()
        
        if not self.su_portal_user_id:
            raise UserError(_('No portal user is linked to this SaaS user record.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Portal User'),
            'res_model': 'res.users',
            'res_id': self.su_portal_user_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': self.env.context,
        }

    def action_view_related_partner(self):
        """
        Open the related portal user record.

        Returns:
            dict: Action to open portal user form view
        """
        self.ensure_one()

        if not self.su_portal_user_id.partner_id:
            raise UserError(_('No partner is linked to this SaaS user record.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Related Partner'),
            'res_model': 'res.partner',
            'res_id': self.su_portal_user_id.partner_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': self.env.context,
        }
