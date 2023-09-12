# -*- coding: utf-8 -*-
{
    'name': 'Resource booking',
    'version': '15.0.1.0',
    'summary': 'Resource booking both internal and in portal.',
    'description': """Customers can book resources or locations in portal based on predefined slots."""
                    """Internal customers can manage customer bookings and make new ones""",
    'license': 'Other proprietary',
    'author': 'Javier L. de los Mozos, Aarón Misis',
    'maintainer': 'Javier L. de los Mozos',
    'website': '',
    'live_test_url':'',
    'category': 'Website/Website',
    'depends': ['website', 'contacts', 'calendar_resource_location_mac5'],
    'data': [
        'data/booking_data.xml',
        'data/booking_crons.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/agenda_views.xml',
        'views/online_booking_views.xml',
        'wizard/close_service_wizard_view.xml',
        'wizard/booking_wizard_view.xml',
#        'config/res_config_settings_views.xml',
        'views/calendar_event_views.xml',
        'views/menues.xml',
        'views/booking_request_view.xml',
        'views/booking_type_view.xml',
        'views/resource_view.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'portal_resource_booking/static/src/xml/search_panel_close_service.xml',
            'portal_resource_booking/static/src/xml/bell_template.xml',
        ],
        'web.assets_frontend': [
            'portal_resource_booking/static/src/scss/frontend_styles.scss',
            'portal_resource_booking/static/src/js/booking_frontend_controller.js',
#            'web/static/lib/fontawesome/css/font-awesome.css',
#            'web_online_appointment_resource/static/lib/datetime/css/datepicker.css',
#            'web_online_appointment_resource/static/lib/datetime/js/bootstrap-datepicker.js',
#            'web_online_appointment_resource/static/lib/datetime/js/locales/bootstrap-datepicker.es.js',
#            'web_online_appointment_resource/static/lib/datetime/js/locales/bootstrap-datepicker.ca.js',
            'portal_resource_booking/static/src/js/select_multiple.js',
        ],
        'web.assets_backend': [
            'portal_resource_booking/static/src/scss/close_service_styles.scss',
            'portal_resource_booking/static/src/js/backend/datepicker_today_patch.js',
        ]
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}