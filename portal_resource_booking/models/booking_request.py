from odoo import models, fields

class BookingRequest(models.Model):
    _name='booking.request'
    
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)