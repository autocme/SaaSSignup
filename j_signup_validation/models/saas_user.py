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
    _order = 'create_date desc'
    _rec_name = 'su_display_name'

    # Basic Information Fields
    su_first_name = fields.Char(
        'First Name',
        required=True,
        help='User\'s first name as provided during registration'
    )
    
    su_last_name = fields.Char(
        'Last Name',
        required=True,
        help='User\'s last name as provided during registration'
    )
    
    su_display_name = fields.Char(
        'Display Name',
        compute='_compute_display_name',
        store=True,
        help='Full name computed from first and last name'
    )
    
    su_email = fields.Char(
        'Email Address',
        required=True,
        help='User\'s email address used for registration and login'
    )
    
    su_phone = fields.Char(
        'Phone Number',
        required=True,
        help='User\'s phone number with international format validation'
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
        help='Indicates if email passed all validation checks'
    )
    
    su_phone_validated = fields.Boolean(
        'Phone Validated',
        default=False,
        help='Indicates if phone number passed validation checks'
    )
    
    su_password_strength = fields.Integer(
        'Password Strength Score',
        default=0,
        help='Password strength score from 0-100 based on validation rules'
    )
    
    # Registration Details
    su_registration_ip = fields.Char(
        'Registration IP',
        help='IP address from which the user registered'
    )
    
    su_registration_date = fields.Datetime(
        'Registration Date',
        default=fields.Datetime.now,
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
        help='Related portal user account created during registration'
    )
    
    su_active = fields.Boolean(
        'Active',
        default=True,
        help='Indicates if the SaaS user record is active'
    )

    @api.depends('su_first_name', 'su_last_name')
    def _compute_display_name(self):
        """
        Compute the display name from first and last name.
        """
        for record in self:
            if record.su_first_name and record.su_last_name:
                record.su_display_name = f"{record.su_first_name} {record.su_last_name}"
            elif record.su_first_name:
                record.su_display_name = record.su_first_name
            elif record.su_last_name:
                record.su_display_name = record.su_last_name
            else:
                record.su_display_name = _('Unnamed User')
        
        _logger.info(f"Computed display names for {len(self)} SaaS user records")

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

    @api.model
    def create_saas_user_with_portal(self, user_data):
        """
        Create a SaaS user record and corresponding portal user.
        
        Args:
            user_data (dict): Dictionary containing user registration data
            
        Returns:
            tuple: (saas_user_record, portal_user_record)
        """
        try:
            _logger.info(f"Creating SaaS user with email: {user_data.get('email')}")
            
            # Create SaaS user record
            saas_user = self.create({
                'su_first_name': user_data.get('first_name'),
                'su_last_name': user_data.get('last_name'),
                'su_email': user_data.get('email'),
                'su_phone': user_data.get('phone'),
                'su_password': user_data.get('password'),  # Should be encrypted
                'su_email_validated': user_data.get('email_validated', False),
                'su_phone_validated': user_data.get('phone_validated', False),
                'su_password_strength': user_data.get('password_strength', 0),
                'su_registration_ip': user_data.get('registration_ip'),
                'su_user_agent': user_data.get('user_agent'),
            })
            
            # Create portal user
            portal_user = self.env['res.users'].create({
                'name': saas_user.su_display_name,
                'login': saas_user.su_email,
                'email': saas_user.su_email,
                'phone': saas_user.su_phone,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
                'active': True,
            })
            
            # Link the records
            saas_user.su_portal_user_id = portal_user.id
            
            _logger.info(f"Successfully created SaaS user {saas_user.id} and portal user {portal_user.id}")
            
            return saas_user, portal_user
            
        except Exception as e:
            _logger.error(f"Error creating SaaS user: {str(e)}")
            raise ValidationError(
                _("Failed to create user account. Please try again or contact support.")
            )

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