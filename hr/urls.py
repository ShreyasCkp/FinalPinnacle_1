# hr/urls.py
from django.urls import path
from . import views



urlpatterns = [    

    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/add/', views.holiday_create, name='holiday_create'),
    path('holidays/edit/<int:pk>/', views.holiday_edit, name='holiday_edit'),
    path('holidays/delete/<int:pk>/', views.holiday_delete, name='holiday_delete'),
    path('leaves/', views.employee_leave_list, name='employee_leave_list'),
    path('leave/edit/<int:leave_id>/', views.employee_leave_create, name='employee_leave_edit'),
    path("leaves/<int:leave_id>/approve/", views.leave_approve, name="leave_approve"),
    path("leaves/<int:leave_id>/reject/", views.leave_reject, name="leave_reject"),
    path('leaves/apply/', views.employee_leave_create, name='employee_leave_create'),
    path('payslip/view/<int:pk>/', views.view_payslip, name='view_payslip'),
    path('payslip/<int:pk>/download/', views.download_payslip, name='download_payslip'),
    path('salary-declarations/', views.salary_declaration_list, name='salary_declaration_list'),
    path('salary-declarations/add/', views.salary_declaration_create, name='salary_declaration_create'),
    path('salary-declarations/<int:pk>/edit/', views.salary_declaration_edit, name='salary_declaration_edit'),
    path('employee-data/', views.get_employee_data, name='get_employee_data'),  # AJAX endpoint
    path('salary-declarations/<int:pk>/delete/', views.salary_declaration_delete, name='salary_declaration_delete'),
    path('employee/calendar/', views.employee_calendar, name='employee_calendar'),
    path('leave/edit/<int:leave_id>/', views.edit_leave_redirect, name='edit_leave_redirect'),
    path('leave/cancel/<int:leave_id>/', views.edit_leave_cancel, name='edit_leave_cancel'),
    path('payslip/<int:month>/<int:year>/download/', views.download_payslip, name='download_payslip'),  
    path('employee-salary-dashboard/', views.employee_salary_dashboard, name='employee_salary_dashboard'),
    path('my-salary-slip/', views.employee_salary_slip_view, name='employee_salary_slip_view'),
    path('dashboard/annual/', views.employee_annual_dashboard, name='employee_annual_dashboard'), 

]
