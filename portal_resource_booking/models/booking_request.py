from odoo import models, fields

class BookingRequest(models.Model):
    _name='booking.request'
    _description = 'Proposed requests from the customer to be shown on bookings.'
    
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)