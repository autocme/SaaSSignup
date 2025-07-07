"""
res.users Model Extension
Extends the res.users model to add bidirectional relation with SaaS User.
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """
    Extend res.users model to add bidirectional relation with SaaS User.
    """
    _inherit = 'res.users'

    # Bidirectional relation with SaaS User
    saas_user_id = fields.Many2one(
        'saas.user',
        string='SaaS User',
        help='Related SaaS User record for this portal user',
        ondelete='cascade'
    )

    def action_view_saas_user(self):
        """
        Action to view the related SaaS User record.
        """
        self.ensure_one()
        if not self.saas_user_id:
            return False
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'SaaS User',
            'res_model': 'saas.user',
            'res_id': self.saas_user_id.id,
            'view_mode': 'form',
            'target': 'current',
        }