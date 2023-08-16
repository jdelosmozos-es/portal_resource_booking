from odoo import models, fields

class BookingType(models.Model):
    _name = 'booking.resource.agenda.type'
    _description = 'Type of agenda, shown in bookings.'
    
    sequence = fields.Integer(string='Sequence', default=1)
    name = fields.Char()