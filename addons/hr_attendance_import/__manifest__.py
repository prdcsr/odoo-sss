{
    'name': 'Attendance Import',
    'author': 'SSS',
    'version': '1.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Import employee attendance',
    'description': 'Import employee attendance',
    'website': 'https://www.yasukapower.com',
    'depends': ['hr', 'hr_attendance', 'hr_contract_types', 'hr_contract', 'ohrms_overtime'],
    'data': [
        'wizard/hr_attendance_import.xml',
        'wizard/hr_attendance_import_solution.xml',
        'wizard/hr_summary_export.xml',
        'wizard/hr_attendance_generate_time_off_view.xml',
        'wizard/hr_attendance_generate_overtime_view.xml',
        'views/hr_attendance_view.xml',
        'views/hr_attendance_template.xml',
        'views/hr_employee_view.xml',
        'views/hr_contracts_view.xml',
        'views/assets_template.xml',
        'views/hr_leave_view.xml',
        'views/hr_overtime_view.xml'
    ],
    'qweb': [
        'static/src/xml/attendance_report_list_controller.xml',
        'static/src/xml/attendance_stats_templates.xml',
        'static/src/xml/leave_summary_template.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}
