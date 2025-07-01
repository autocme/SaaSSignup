"""
J Signup Field Model
Defines individual dynamic fields for the signup form
"""

from odoo import api, fields, models


class JSignupField(models.Model):
    """
    J Signup Field model for defining dynamic signup form fields.
    This model represents individual fields that can be added to the signup form.
    """
    _name = 'j.signup.field'
    _description = 'J Signup Dynamic Field'
    _rec_name = 'jsf_label'
    _order = 'jsf_sequence, id'

    jsf_sequence = fields.Integer(
        'Sequence',
        default=10,
        help='Order of the field in the signup form'
    )
    
    jsf_field_id = fields.Many2one(
        'ir.model.fields',
        'Source Field',
        required=True,
        domain=[
            ('model_id.model', '=', 'res.users'),
            ('ttype', 'in', ['char', 'integer', 'float', 'text', 'date', 'datetime', 'binary', 'boolean', 'selection'])
        ],
        help='The res.users field that this signup field represents'
    )
    
    jsf_label = fields.Char(
        'Field Label',
        help='Custom label for the field (if empty, uses field description)'
    )
    
    jsf_placeholder = fields.Char(
        'Placeholder Text',
        help='Placeholder text to show in the input field'
    )
    
    jsf_help_text = fields.Text(
        'Help Text',
        help='Additional help text to display below the field'
    )
    
    jsf_field_type = fields.Char(
        'Field Type',
        related='jsf_field_id.ttype',
        readonly=True,
        store=True,
        help='Technical type of the field'
    )
    
    jsf_field_name = fields.Char(
        'Field Name',
        related='jsf_field_id.name',
        readonly=True,
        store=True,
        help='Technical name of the field'
    )
    
    jsf_required = fields.Boolean(
        'Required',
        default=False,
        help='Whether this field is required in the signup form'
    )
    
    jsf_active = fields.Boolean(
        'Active',
        default=True,
        help='Whether this field is active and should appear in the form'
    )
    
    jsf_configuration_id = fields.Many2one(
        'j.signup.configuration',
        'Configuration',
        required=True,
        ondelete='cascade',
        help='The signup configuration this field belongs to'
    )
    
    jsf_column_width = fields.Selection([
        ('col-12', 'Full Width (12/12)'),
        ('col-6', 'Half Width (6/12)'),
        ('col-4', 'Third Width (4/12)'),
        ('col-3', 'Quarter Width (3/12)'),
    ], 'Column Width', 
        default='col-12',
        help='Bootstrap column width for the field'
    )

    @api.onchange('jsf_field_id')
    def _onchange_jsf_field_id(self):
        """
        Set default label when field is selected.
        """
        if self.jsf_field_id and not self.jsf_label:
            self.jsf_label = self.jsf_field_id.field_description

    def get_field_html_attributes(self):
        """
        Get HTML attributes for the field based on its configuration.
        
        Returns:
            dict: Dictionary of HTML attributes
        """
        attrs = {
            'name': self.jsf_field_name,
            'id': f'dynamic_{self.jsf_field_name}',
            'placeholder': self.jsf_placeholder or self.jsf_label or '',
        }
        
        if self.jsf_required:
            attrs['required'] = 'required'
        
        # Set input type based on field type
        if self.jsf_field_type == 'char':
            attrs['type'] = 'text'
        elif self.jsf_field_type == 'integer':
            attrs['type'] = 'number'
            attrs['step'] = '1'
        elif self.jsf_field_type == 'float':
            attrs['type'] = 'number'
            attrs['step'] = 'any'
        elif self.jsf_field_type == 'text':
            attrs['type'] = 'textarea'
        elif self.jsf_field_type == 'date':
            attrs['type'] = 'date'
        elif self.jsf_field_type == 'datetime':
            attrs['type'] = 'datetime-local'
        elif self.jsf_field_type == 'binary':
            attrs['type'] = 'file'
        elif self.jsf_field_type == 'boolean':
            attrs['type'] = 'checkbox'
        
        return attrs

    def get_field_input_html(self):
        """
        Generate HTML input element for this field.
        
        Returns:
            str: HTML string for the input element
        """
        attrs = self.get_field_html_attributes()
        
        if self.jsf_field_type == 'text':
            return f'<textarea class="form-control" name="{attrs["name"]}" id="{attrs["id"]}" placeholder="{attrs["placeholder"]}" {"required" if self.jsf_required else ""}></textarea>'
        elif self.jsf_field_type == 'boolean':
            return f'<input type="checkbox" class="form-check-input" name="{attrs["name"]}" id="{attrs["id"]}" value="1" {"required" if self.jsf_required else ""}>'
        elif self.jsf_field_type == 'selection':
            # For selection fields, we need to get the selection options
            return f'<select class="form-control" name="{attrs["name"]}" id="{attrs["id"]}" {"required" if self.jsf_required else ""}><option value="">Select...</option></select>'
        else:
            attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
            return f'<input class="form-control" {attr_str}>'