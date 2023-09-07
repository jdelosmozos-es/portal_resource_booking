from odoo import fields, models, api, _
from datetime import timedelta, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from babel.dates import format_date

class CalendarEvent(models.Model):
    _name = 'calendar.event'
    _inherit = ["mail.activity.mixin","calendar.event"]
    _order = 'start'
    
    STATE_SELECTION = [
        ('needsAction', 'Needs Action'),
        ('declined', 'Declined'),
        ('acc_from_cust', 'Accepted from customer'),
        ('acc_from_res_mgr', 'Accepted from reservations manager'),
        ('fully_accepted', 'Fully accepted'),
        ('customer_arrived', 'Customer arrived'),
        ('customer_not_shown', 'Customer not shown'),
    ]

    def _get_default_state(self):
        if self.is_from_reservation_system:
            return 'needsAction'
        else:
            return False
        
    resource = fields.Many2one(
        comodel_name="calendar.event.location",
        string="Space", readonly=True
    )
    resource_occupancy = fields.Integer('Resource occupancy', readonly=True)
    state = fields.Selection(STATE_SELECTION, string='Status', default=_get_default_state, readonly=True)
    additional_information = fields.Text(readonly=True)
    is_from_reservation_system = fields.Boolean(readonly=True)
    slots = fields.Many2many(comodel_name='booking.resource.agenda.slot',readonly=True)
    requests = fields.Many2many(comodel_name='booking.request')
    special_request = fields.Char()
    time_dependant_status = fields.Boolean(compute='_compute_status')
    customer = fields.Many2one(comodel_name='res.partner',compute='_compute_customer')
    agenda = fields.Many2one(comodel_name='booking.resource.agenda', compute='_compute_agenda')
    service = fields.Many2one(comodel_name='booking.resource.service', readonly=True)
    #En realidad es un compute pero no se puede hacer así porque siempre se llama al create desde ptython y eso hacer que no se llame al compute, y lo necesito almacenado
    service_type = fields.Many2one(comodel_name='booking.resource.agenda.type', related='service.type')
    
    @api.model
    def search_panel_select_multi_range(self, field_name, **kwargs):
        res = super(CalendarEvent, self).search_panel_select_multi_range(field_name,**kwargs)
        if self._name == 'calendar.event':
            for record in res['values']:
                record['closed_service'] = self.env['booking.resource.service'].browse(record['id']).get_is_closed()
                record['display_name'] = record['display_name'].split(' - ')[1]
                if 'group_name' in record:
                    record['group_name'] = format_date(record['group_name'],locale=self.env.user.lang)
        return res
    
    @api.depends('slots')
    def _compute_agenda(self):
        for record in self:
            if record.is_from_reservation_system:
                record.agenda = record.slots.mapped('agenda')
            else:
                record.agenda = False
                
    @api.depends('allday', 'start', 'stop')
    def _compute_dates(self):
        """ Adapt the value of start_date(time)/stop_date(time)
            according to start/stop fields and allday. Also, compute
            the duration for not allday meeting ; otherwise the
            duration is set to zero, since the meeting last all the day.
        """
        """ Modificado para que se calculen siempre las fechas en caso de reservas"""
        for meeting in self:
            if meeting.is_from_reservation_system:
                meeting.start_date = meeting.start.date()
                meeting.stop_date = meeting.stop.date()
            else:
                if meeting.allday and meeting.start and meeting.stop:
                    meeting.start_date = meeting.start.date()
                    meeting.stop_date = meeting.stop.date()
                else:
                    meeting.start_date = False
                    meeting.stop_date = False
                
    @api.depends('attendee_ids')
    def _compute_customer(self):
        for record in self:
            if record.is_from_reservation_system:
                for attendee in record.attendee_ids:
                    if record._is_management(attendee):
                        continue
                    else:
                        record.customer = attendee.partner_id
            else:
                record.customer = False
    
    def _compute_status(self):
        for record in self:
            #TODO: buscar los slots de hoy con state= fully_accepted and start_datetime < now
            # ponerles estado ¿cliente ha llegado? ¿o poner el iteral cliente debería haber llegado?
            record.time_dependant_status = False
    
    def liberate_slots(self):
        for slot in self.slots:
            new_occupancy = slot.occupancy - self.resource_occupancy
            slot.occupancy = new_occupancy
            
    def _is_management(self,attendee):
        management_user = self.env.ref('portal_resource_booking.appointment_manager_user')
        mgmt_attendee = self.attendee_ids.filtered(lambda x: x.partner_id.id == management_user.partner_id.id)
        if attendee == mgmt_attendee:
            return True
        else:
            return False
        
    def _update_state(self, changer, status):      
        if self._is_management(changer):
            if status == 'accepted':
                if self.state == 'acc_from_cust':
                    self.write({'state': 'fully_accepted'})
                else:
                    self.write({'state': 'acc_from_res_mgr'})
            elif status == 'tentative':
                if self.state == 'fully_accepted':
                    self.write({'state': 'acc_from_cust'})
                elif self.state == 'acc_from_res_mgr':
                    self.write({'state': 'needsAction'})
        else:
            if status in ['declined', 'tentative']:
                self.write({'state': 'declined'})
                manager_att = self.attendee_ids.filtered(lambda x: x != changer)
                manager_att.write({'state': 'needsAction'})
            else:
                if self.state == 'acc_from_res_mgr':
                    self.write({'state': 'fully_accepted'})
                else:
                    self.write({'state': 'acc_from_cust'})
        return True
    
    def create_activity(self, user, message):
        activity_type =  self.env.ref('mail.mail_activity_data_todo')
        self.env['mail.activity'].sudo().create({
            'activity_type_id': activity_type.id,
            'date_deadline': fields.Date.context_today(self),
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].sudo().search([('model','=', 'calendar.event')]).id,
            'user_id': user.id,
            'summary': message,
        })
        #TODO: remove message_post asociados
        
    def do_customer_not_shown(self):
        return self.write({'state': 'customer_not_shown'})
    
    def is_short_notice(self, vals):
        start_date = datetime.strptime(vals['start'], DEFAULT_SERVER_DATETIME_FORMAT)
        alarm_minutes = self.env['ir.config_parameter'].sudo().get_param('portal.resource.booking.short_notice_alarm_minutes')
        if fields.Datetime.now() + timedelta(minutes=int(alarm_minutes)) > start_date:
            return True
        else:
            return False
        
    @api.model   
    def create(self, vals):
        if 'is_from_reservation_system' in vals and vals['is_from_reservation_system']:
            vals['state'] = 'needsAction'
            start_date = fields.Datetime.to_datetime(vals['start']).date()
            agenda = self.env['booking.resource.agenda.slot'].search([('id','in',vals['slots'])]).mapped('agenda')[0]
            services = self.env['booking.resource.service'].search([('agenda','=',agenda.id),('date','=',start_date)])
            if services:
                vals['service']=services[0].id
            res = super(CalendarEvent, self).create(vals)
            management_user = self.env.ref('portal_resource_booking.appointment_manager_user')
            target = management_user.partner_id
            title = _('Reservation system message')
            sticky = True
            if self.is_short_notice(vals):
                message = _('New booking received on short notice')
                type_message = 'danger'
                bus_message = {
                    "type": type_message,
                    "message": message,
                    "title": title,
                    "sticky": sticky,
                }
                notifications = [[partner, "web.notify", [bus_message]] for partner in target]
                self.env["bus.bus"]._sendmany(notifications)
            res.create_activity(management_user, _('New booking. Confirm or cancel.'))
        else:
            vals['state'] = False
            res = super(CalendarEvent, self).create(vals)
        return res
    
    def unlink(self):
        for record in self:
            if record.is_from_reservation_system:
                record.liberate_slots()
        return super(CalendarEvent, self).unlink()
    
    def write(self, vals):
        if self.is_from_reservation_system:
            if 'active' in vals:
                if vals['active']:
                    for line in self.slots:
                        new_occupancy = line.occupancy + self.resource_occupancy
                        line.occupancy = new_occupancy
                else:
                    for line in self.slots:
                        new_occupancy = line.occupancy - self.resource_occupancy
                        line.occupancy = new_occupancy
            if 'start' in vals or 'stop' in vals:
                raise UserError(_('Is not supported to modify the booking. You shoud cancel and create a new one instead.'))
        return super(CalendarEvent, self).write(vals)
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        return super(CalendarEvent, self.sudo()).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
    