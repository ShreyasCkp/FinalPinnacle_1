
from django.urls import path
from . import views
 
urlpatterns = [
   
    path('student-login/', views.student_login_view, name='student_login_view'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/set-password/', views.student_set_password, name='student_set_password'),
    path('student/set-passcode/', views.student_set_passcode, name='student_set_passcode'),
    path('student/password-reset/', views.student_password_reset_view, name='student_password_reset_view'),

    path('student/change-password/', views.student_change_password, name='student_change_password'),
    path('student/change-passcode/', views.student_change_passcode, name='student_change_passcode'),


    path('student/attendance/', views.my_attendance_view, name='my_attendance_view'),
    path('student/fees/',views.my_fees_view, name='my_fees_view'),
    path('student/profile/', views.student_profile_view, name='student_profile_view'),

    path('student/assignments/', views.my_assignments_view, name='my_assignments_view'),
    path('submit-assignment/<int:assignment_id>/', views.submit_assignment_view, name='submit_assignment'),


    #grade
    path('student/grades/', views.my_grades_view, name='my_grades_view'),
    path('student/study-materials/', views.my_study_materials_view, name='my_study_materials_view'),
    path('student/certificates/', views.my_certificates_view, name='my_certificates_view'),
    #
    path('assignments/add/', views.create_assignment, name='create_assignment'),
    path('Assignments_List/', views.assignment_list, name='assignment_list'),
    path('assignments/delete/<int:pk>/', views.delete_assignment, name='delete_assignment'),
    path('assignments/<int:pk>/edit/', views.edit_assignment, name='edit_assignment'),
    path('assignments/<int:pk>/view/', views.view_assignment, name='view_assignment'),

    #lib
        path('library', views.book_list, name='book_list'),
    path('library/add', views.add_book, name='add_book'),
    path('library/view/<int:pk>', views.book_view, name='book_view'),
    path('library/edit/<int:pk>', views.book_update, name='book_update'),
    path('library/delete/<int:pk>', views.book_delete, name='book_delete'),

        path('books/<int:book_id>/borrow-details/', views.book_borrow_details, name='book_borrow_details'),

     path('borrow/new/', views.borrow_book_view, name='borrow_book'),
path('borrow/<int:record_id>/details/', views.borrow_record_details, name='borrow_record_details'),

    #this is pdf 
    # path('study-materials/', views.employee_study_material_list, name='employee_study_material_list'),
    # path('study-materials/create/', views.create_or_edit_study_material, name='create_or_edit_study_material'),
    # path('study-materials/edit/<int:pk>/', views.create_or_edit_study_material, name='create_or_edit_study_material'),
    # path('study-materials/delete/<int:pk>/', views.delete_employee_study_material, name='delete_employee_study_material'),

    path('study-material/create/', views.create_study_material, name='create_study_material'),
    path('study-material/edit/<int:pk>/', views.edit_study_material, name='edit_study_material'),
    # optionally: delete
    path('study-material/delete/<int:pk>/', views.delete_employee_study_material, name='delete_employee_study_material'),
    # optionally: list
    path('study-material/list/', views.employee_study_material_list, name='employee_study_material_list'),

    #This is exam
    path('exam/create/', views.create_exam, name='create_exam'),
    path('exam/', views.exam_list, name='exam_list'),
    path('exam/<int:pk>/edit/', views.edit_exam, name='edit_exam'),
    path('exam/<int:pk>/view/', views.view_exam, name='view_exam'),
    path('exam/<int:pk>/delete/', views.delete_exam, name='delete_exam'),

    #student assignmnet view the faculty
    # path('submitted-assignments/', views.submitted_assignments_view, name='submitted_assignments_view'),
    # urls.py
    path('assignments/<int:assignment_id>/submissions/', views.submitted_assignments, name='submitted_assignments'),


    #exam add
    # List all exam marks
    path('exam-marks/', views.exam_marks_list, name='exam_marks_list'),

    # Create new exam marks
    path('exam-marks/create/', views.create_exam_marks, name='create_exam_marks'),

    # Edit existing exam marks
    path('exam-marks/edit/<int:pk>/', views.edit_exam_marks, name='edit_exam_marks'),

    # View exam marks details
    path('exam-marks/view/<int:pk>/', views.view_exam_marks, name='view_exam_marks'),

    # Delete exam marks
    path('exam-marks/delete/<int:pk>/', views.delete_exam_marks, name='delete_exam_marks'),
    path('calendar/form', views.student_calendar_form, name='student_calendar_form'),

    path('student/leave/create/', views.student_leave_create, name='student_leave_create'),
    path('student/leave/list/', views.student_leave_list, name='student_leave_list'),
     # Faculty/Admin side
    path('leave/requests/', views.leave_approval_list, name='leave_approval_list'),
    path('leave/<int:pk>/approve/', views.approve_leave, name='approve_leave'),
    path('leave/<int:pk>/reject/', views.reject_leave, name='reject_leave'),
    path('student/leave/edit/<int:pk>/', views.student_leave_edit, name='student_leave_edit'),
    path('student/notification/read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),

# urls.py
path('student/leave/<int:pk>/cancel/', views.student_leave_cancel, name='student_leave_cancel'),
path('employee-login/', views.employee_login_view, name='employee_login_view'),
    path('employee/logout/', views.employee_logout, name='employee_logout'),
    path('employee/set-password/', views.employee_set_password, name='employee_set_password'),
    path('employee/set-passcode/', views.employee_set_passcode, name='employee_set_passcode'),
    path('employee-dashboard/', views.employee_dashboard_view, name='employee_dashboard_view'),
    path('employee/password-reset/', views.employee_password_reset_view, name='employee_password_reset_view'),
     path('profile/', views.employee_profile, name='employee_profile'),
  # employee/urls.py


  path('employee/attendance/', views.employee_attendance_view, name='employee_attendance_view'),
    path('assignments/<int:assignment_id>/download/', views.download_assignment, name='download_assignment'),
    path("assignment/<int:assignment_id>/mark-in-progress/", views.mark_in_progress, name="mark_in_progress"),


    path('employee-login/', views.employee_login_view, name='employee_login_view'),
    path('employee/logout/', views.employee_logout, name='employee_logout'),
    path('employee/set-password/', views.employee_set_password, name='employee_set_password'),
    path('employee/set-passcode/', views.employee_set_passcode, name='employee_set_passcode'),
    path('employee-dashboard/', views.employee_dashboard_view, name='employee_dashboard_view'),
    path('employee/password-reset/', views.employee_password_reset_view, name='employee_password_reset_view'),

    path('assignments/<int:assignment_id>/download/', views.download_assignment, name='download_assignment'),
    path("assignment/<int:assignment_id>/mark-in-progress/", views.mark_in_progress, name="mark_in_progress"),

      path("assignment/<int:assignment_id>/mark-in-progress/", views.mark_in_progress, name="mark_in_progress"),
            path("certificate/", views.student_certificate_view, name="student_certificate_view"),
    path("employee/all-student-marks/", views.employee_all_student_view, name="employee_all_student_view"),
            path("mypage/", views.show_page, name="show_page"),   # ?? name is important


         #certificate marks enter
    path("student-marks-entry/", views.student_marks_entry, name="student_marks_entry"),
    path('student-marks/', views.student_marks_list, name='student_marks_list'),
    path("marks/<int:pk>/", views.student_marks_view, name="student_marks_view"), # view
    path("marks/<int:pk>/edit/", views.student_marks_edit, name="student_marks_edit"),   # edit
    path("marks/<int:pk>/delete/", views.student_marks_delete, name="student_marks_delete"), # delete

    #certificate download 
    path("marksheet/<int:student_id>/", views.student_marksheet_view, name="student_marksheet_view"),
    path("marksheet/<int:student_id>/pdf/", views.student_marksheet_pdf, name="student_marksheet_pdf"),


     # Student-facing library
path('student/library/', views.student_book_list, name='student_book_list'),
path('student/library/<int:pk>/', views.student_book_detail, name='student_book_detail'),


  path('employee/change-password/', views.employee_change_password, name='employee_change_password'),
    path('employee/change-passcode/', views.employee_change_passcode, name='employee_change_passcode'),

    path('settings/', views.settings_view, name='settings'),




]


