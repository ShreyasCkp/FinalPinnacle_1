from django.urls import path
from .views import generate_qr_dynamic
from django.urls import re_path
from . import views


urlpatterns = [
     path('bulk-import', views.bulk_import_admissions, name='bulk_import_admissions'),
      path('pu-application/form', views.admission_form, name='admission_form'),  # for blank form
      path('pu-applicaion/form/<str:enquiry_no>', views.admission_form, name='admission_form'),  # for pre-filled form
      

     path('pu-application/list/', views.admission_list, name='admission_list'),
     path('pu-application/form/<int:pk>/view', views.view_pu_admission, name='view_pu_admission'), 
     path('pu-application/form/<int:pk>/edit', views.edit_pu_admission, name='edit_pu_admission'),
      path('pu-application/form/<int:pk>/delete', views.delete_pu_admission,name="delete_pu_admission"),
     

       path('bcom-application/form', views.degree_admission_form, name='degree_admission_form'),  # blank form
    path('bcom-application/form/<str:enquiry_no>', views.degree_admission_form, name='degree_admission_form'),  # prefilled form\
           path('bcom-application/<int:pk>/view', views.view_degree_admission, name='view_degree_admission'), # prefilled form\

    path('bcom-application/form/<int:pk>/edit', views.edit_degree_admission, name='edit_degree_admission'),    
    path('bcom-application/form/<int:pk>/delete', views.delete_degree_admission, name='delete_degree_admission'),
     path('fee-management', views.fee_management, name='fee_management'),


path('enquiry/convert/<str:enquiry_no>', views.convert_enquiry, name='convert_enquiry'),



      path('bcom-application-list', views.degree_admission_list, name='degree_admission_list'),
     path('shortlisted', views.shortlisted_students_view, name='shortlisted_students_view'),
    path('approve/<str:stream>/<int:student_id>', views.approve_student, name='approve_student'),
     # path('enquiry/', views.enquiry_form_view, name='enquiry_form'),
    path('confirmed-applications-fee-entry', views.shortlist_display, name='shortlist_display'),

    path('pu-fee/<int:admission_id>', views.pu_fee_detail_form, name='pu_fee_detail_form'),
    path('degree-fee/<int:admission_id>', views.degree_fee_detail_form, name='degree_fee_detail_form'),

 
    #   path('enquiries/', views.enquiry_list, name='enquiry_list'),
    path('ajax/load-courses', views.load_courses, name='ajax_load_courses'),
     path('api/enquiry-lookup', views.enquiry_lookup, name='enquiry_lookup'),
     path('degree-enquiry-lookup', views.degree_enquiry_lookup, name='degree_enquiry_lookup'),


    # path('fee/view/<int:fee_id>/', views.view_fee_detail, name='view_fee_detail'),
       path('admission/send_bulk_emails', views.send_bulk_emails, name='send_bulk_emails'),

   # path('admission/create-logins/',views. create_student_logins, name='create_student_logins'),

    path('admission/student-login', views.student_login, name='student_login'),
    path('admissions/reset-password', views.reset_password, name='reset_password'),


        #Fee
   
    path('get_student_details', views.get_student_details, name='get_student_details'),
    path('generate_qr_dynamic', generate_qr_dynamic, name='generate_qr_dynamic'),
    # path('receipt/<int:student_id>/pdf', views.generate_fee_receipt_pdf, name='generate_fee_receipt_pdf'), # PDF Receipt

    path('save-payment', views.save_payment, name='save_payment'),

    # path('receipt/student/<int:pk>', views.download_student_receipt, name='download_student_receipt'),
    # path('receipt/admin/<int:pk>', views.download_admin_receipt, name='download_admin_receipt'),

   path('enquiry-print-form', views.enquiry_print_form, name='enquiry_print_form'),

      path('export-payments', views.export_payments_excel, name='export_payments_excel'),
 #export all payments getting total paid and pending fee
   path('export-payments', views.export_payments_excel, name='export_payments_excel'),

   path('admission', views.admission_dashboard, name='admission_dashboard'),

       path('pending-applications', views.pending_admissions, name='pending_admissions'),
    path('confirmed-Admissions', views.confirmed_admissions, name='confirmed_admissions'),
   path('generate-userid/<path:admission_no>', views.generate_student_userid, name='generate_student_userid'),
    # urls.py

            #Fee
           #Fee
 path('student-fee-payment-history', views.student_fee_form_view, name='student_fee_form_view'),
path('student-fee-form/add', views.student_fee_form_add, name='student_fee_form_add'),
path('student-fee-form/edit/<str:admission_no>', views.student_fee_form_edit, name='student_fee_form_edit'),
path('student-fee-form/list', views.student_list, name='student_list'),
path('student-fee-form/delete/<str:admission_no>', views.student_fee_form_delete, name='student_fee_form_delete'),
        # fee application admission
    path('degree-admission/<path:admission_no>/receipt-pdf', views.download_degree_admission_fee_receipt, name='degree_admission_fee_receipt'),
   
     path('admission/pu-fee-receipt/<path:admission_no>', views.download_pu_admission_fee_receipt, name='download_pu_admission_fee_receipt'),






    path('enquiry-form/delete/<str:enquiry_no>', views.enquiry_form_delete, name='enquiry_form_delete'),
path('enquiry-form/edit/<str:enquiry_no>', views.enquiry_form_edit, name='enquiry_form_edit'),


       path('enquiry-form/view/<str:enquiry_no>', views.enquiry_form_view, name='enquiry_form_view'),
    
 path('pu-enquiry-form', views.enquiry_form_add, name='enquiry_form_add'),
  path('b.com-enquiry-add', views.degree_enquiry_add, name='degree_enquiry_add'),



     path('enquiries-list', views.enquiry_list, name='enquiry_list'),


      path('converted-enquiries-list', views.converted_enquiry_list, name='converted_enquiry_list'),



      path('get-student-name', views.get_student_name, name='get_student_name'),
          path('schedule-follow-up-form', views.schedule_follow_up_form_add, name='schedule_follow_up_form_add'),
path('follow-list', views.follow_up_list, name='follow_up_list'),
path('schedule-follow-up-form/view/<int:pk>', views.schedule_follow_up_form_view, name='schedule_follow_up_form_view'),

 path('schedule-follow-up-form/edit/<int:pk>', views.schedule_follow_up_form_edit, name='schedule_follow_up_form_edit'),
    path('schedule-follow-up-form/delete/<int:pk>', views.schedule_follow_up_form_delete, name='schedule_follow_up_form_delete'),

path('follow-up-history', views.follow_up_list, name='follow_up_list'),

path('followups-list', views.followups_due_list, name='followups_due_list'),
   path('pending-followup-list', views.pending_followups_list, name='pending_followups_list'),
path('followup/<int:id>/update-status', views.update_followup_status, name='update_followup_status'),
 # path('dashboard_view_follow_up/', views.dashboard_view_follow_up, name='dashboard_view_follow_up'),

   path('student-enquiry-management', views.enquiry_dashboard, name='enquiry_dashboard'),
   path('ajax/load-courses', views.load_courses, name='ajax_load_courses'),
   path('ajax/load-courses-degree', views.load_courses_degree, name='ajax_load_courses_degree'),
    path("admissions/reports", views.reports, name="reports"),


     path('total-enquiries-list', views.enquiry_list1, name='enquiry_list1'),

     path('send-whatsapp-message/<str:enquiry_no>/', views.send_whatsapp_message, name='send_whatsapp_message'),


   path('fee-dashboard', views.dashboard_view, name='fee_dashboard'),


   re_path(r'^admission/pu-fee-receipt/(?P<admission_no>[^/]+)/$',views.download_pu_admission_fee_receipt,name='download_pu_admission_fee_receipt'),

   re_path(r'^generate-userid/(?P<admission_no>[\w\-]+)/$', views.generate_student_userid, name='generate_student_userid'),

   path('fee-management/', views.fee_management, name='fee_management'),


       path('get-course-types-by-academic', views.get_course_types_by_academic, name='get_course_types_by_academic'),
    path('get-courses-by-type', views.get_courses_by_type, name='get_courses_by_type'),
   # urls.py
path('ajax/get_sem_by_course', views.get_sem_by_course, name='get_sem_by_course'),

     path('student-fee-list', views.student_fee_list, name='student_fee_list'),

path('ajax/get-courses', views.get_courses_by_type, name='get_courses_by_type'),










path('get-course-fees', views.get_fees_for_course_type, name='get_course_fees'),

path('fee-collection/collect', views.fee_collection_collect, name='fee_collection_collect'),


path('collect-fee-payment', views.collect_fee_payment_page, name='collect_fee_payment_page'),





path('collect-fee-payment-ajax', views.collect_fee_payment_ajax, name='collect_fee_payment_ajax'),

    path("send-admission-email/<int:admission_id>/", views.send_admission_email, name="send_admission_email"),

 path('ajax/load-courses/', views.ajax_load_courses, name='ajax_load_courses'),
]



