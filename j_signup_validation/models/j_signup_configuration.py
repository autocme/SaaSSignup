"""
J Signup Configuration Model
Allows dynamic configuration of additional signup fields
"""

from odoo import fields, models


class JSignupConfiguration(models.Model):
    """
    J Signup Configuration model for managing dynamic signup fields.
    This model allows administrators to configure additional fields
    that should appear in the custom signup form.
    """
    _name = 'j.signup.configuration'
    _description = 'J Signup Configuration'
    _rec_name = 'jsc_name'

    jsc_name = fields.Char(
        'Configuration Name',
        required=True,
        default='Default Signup Configuration',
        help='Name of this signup configuration'
    )
    
    jsc_active = fields.Boolean(
        'Active',
        default=True,
        help='Whether this configuration is active'
    )
    
    jsc_signup_field_ids = fields.One2many(
        'j.signup.field',
        'jsf_configuration_id',
        'Dynamic Signup Fields',
        help='Additional fields to display in the signup form'
    )
    
    jsc_description = fields.Text(
        'Description',
        help='Description of this signup configuration'
    )

    def get_active_configuration(self):
        """
        Get the active signup configuration.
        
        Returns:
            recordset: Active configuration record or empty recordset
        """
        return self.search([('jsc_active', '=', True)], limit=1)

    def get_dynamic_fields(self):
        """
        Get list of dynamic fields for the active configuration.
        
        Returns:
            list: List of field dictionaries with field information
        """
        active_config = self.get_active_configuration()
        if not active_config:
            return []
        
        fields_data = []
        for field_config in active_config.jsc_signup_field_ids.filtered('jsf_active'):
            fields_data.append({
                'field_name': field_config.jsf_field_id.name,
                'field_label': field_config.jsf_label or field_config.jsf_field_id.field_description,
                'field_type': field_config.jsf_field_type,
                'placeholder': field_config.jsf_placeholder,
                'help_text': field_config.jsf_help_text,
                'required': field_config.jsf_required,
                'field_id': field_config.id,
            })
        
        return fields_data