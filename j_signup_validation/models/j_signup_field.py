"""
Signup Field Model
Defines individual dynamic fields for the signup form
"""

from odoo import api, fields, models


class SignupField(models.Model):
    """
    Signup Field model for defining dynamic signup form fields.
    This model represents individual fields that can be added to the signup form.
    """
    _name = 'signup.field'
    _description = 'Signup Dynamic Field'
    _rec_name = 'label'
    _order = 'sequence, id'

    sequence = fields.Integer(
        'Sequence',
        default=10,
        help='Order of the field in the signup form'
    )
    
    field_id = fields.Many2one(
        'ir.model.fields',
        'Source Field',
        required=True,
        ondelete='cascade',
        domain=[
            ('model_id.model', '=', 'res.users'),
            ('ttype', 'in', ['char', 'integer', 'float', 'text', 'date', 'datetime', 'binary', 'boolean',])
        ],
        help='The res.users field that this signup field represents'
    )
    
    label = fields.Char(
        'Field Label',
        help='Custom label for the field (if empty, uses field description)'
    )
    
    placeholder = fields.Char(
        'Placeholder Text',
        help='Placeholder text to show in the input field'
    )
    
    help_text = fields.Text(
        'Help Text',
        help='Additional help text to display below the field'
    )
    
    field_type = fields.Selection(
        string='Field Type',
        related='field_id.ttype',
        readonly=True,
        store=True,
        help='Technical type of the field'
    )
    
    field_name = fields.Char(
        'Field Name',
        related='field_id.name',
        readonly=True,
        store=True,
        help='Technical name of the field'
    )
    
    required = fields.Boolean(
        'Required',
        default=False,
        help='Whether this field is required in the signup form'
    )
    
    active = fields.Boolean(
        'Active',
        default=True,
        help='Whether this field is active and should appear in the form'
    )
    
    configuration_id = fields.Many2one(
        'signup.configuration',
        'Configuration',
        required=True,
        ondelete='cascade',
        help='The signup configuration this field belongs to'
    )
    


    @api.onchange('field_id')
    def _onchange_field_id(self):
        """
        Set default label when field is selected.
        """
        if self.field_id and not self.label:
            self.label = self.field_id.field_description

    def get_field_html_attributes(self):
        """
        Get HTML attributes for the field based on its configuration.
        
        Returns:
            dict: Dictionary of HTML attributes
        """
        attrs = {
            'name': self.field_name,
            'id': f'dynamic_{self.field_name}',
            'placeholder': self.placeholder or self.label or '',
        }
        
        if self.required:
            attrs['required'] = 'required'
        
        # Set input type based on field type
        if self.field_type == 'char':
            attrs['type'] = 'text'
        elif self.field_type == 'integer':
            attrs['type'] = 'number'
            attrs['step'] = '1'
        elif self.field_type == 'float':
            attrs['type'] = 'number'
            attrs['step'] = 'any'
        elif self.field_type == 'text':
            attrs['type'] = 'textarea'
        elif self.field_type == 'date':
            attrs['type'] = 'date'
        elif self.field_type == 'datetime':
            attrs['type'] = 'datetime-local'
        elif self.field_type == 'binary':
            attrs['type'] = 'file'
        elif self.field_type == 'boolean':
            attrs['type'] = 'checkbox'
        
        return attrs

    def get_field_input_html(self):
        """
        Generate HTML input element for this field.
        
        Returns:
            str: HTML string for the input element
        """
        attrs = self.get_field_html_attributes()
        
        if self.field_type == 'text':
            return f'<textarea class="form-control" name="{attrs["name"]}" id="{attrs["id"]}" placeholder="{attrs["placeholder"]}" {"required" if self.required else ""}></textarea>'
        elif self.field_type == 'boolean':
            return f'<input type="checkbox" class="form-check-input" name="{attrs["name"]}" id="{attrs["id"]}" value="1" {"required" if self.required else ""}>'
        elif self.field_type == 'selection':
            # For selection fields, we need to get the selection options
            return f'<select class="form-control" name="{attrs["name"]}" id="{attrs["id"]}" {"required" if self.required else ""}><option value="">Select...</option></select>'
        else:
            attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
            return f'<input class="form-control" {attr_str}>'