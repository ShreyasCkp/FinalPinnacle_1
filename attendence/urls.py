# urls.py
from django.urls import path
from . import views
from .views import student_attendance_form_view ,student_attendance_list

urlpatterns = [
   

         
   path('employee-attendance-list', views.employee_attendance_list, name='employee_attendance_list'),
   path('employee-attendance-add', views.employee_attendance_form_add, name='employee_attendance_form_add'),
   path('employee-attendance/view/<int:pk>', views.employee_attendance_form_view, name='employee_attendance_form_view'),
   path('employee-attendance/edit/<int:pk>', views.employee_attendance_form_edit, name='employee_attendance_form_edit'),
path('employee-attendance/delete/<int:pk>', views.employee_attendance_form_delete, name='employee_attendance_form_delete'),


    path('api/employee/<int:pk>', views.employee_detail_api),
    path('attendance/settings', views.attendance_settings_view, name='attendance_settings_view'),
     path('campus-attendance-management', views.attendance_dashboard, name='attendance_dashboard'),
     path('attendance-reports', views.attendance_report, name='attendance_report'),

       path('student-attendance-list', views.student_attendance_list, name='student_attendance_list'),
    path('student-attendance/add', views.student_attendance_form_add, name='student_attendance_form_add'),
    path('student_attendance/edit/<int:record_id>', views.student_attendance_form_edit, name='student_attendance_form_edit'),
path('student_attendance/view/<int:record_id>', views.student_attendance_form_view, name='student_attendance_form_view'),
path('student_attendance/delete/<int:record_id>', views.student_attendance_form_delete, name='student_attendance_form_delete'),







     
]

