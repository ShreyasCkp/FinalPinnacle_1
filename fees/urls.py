
from django.urls import path,re_path
from . import views
from master.views import get_semesters_by_course
from .views import generate_receipt
 
urlpatterns = [
    path('-declarations', views.fee_declaration_list, name='fee_declaration_list'),
    path('-declarations/add', views.fee_declaration_add, name='fee_declaration_add'),
    path('-declarations/edit/<int:pk>', views.fee_declaration_edit, name='fee_declaration_edit'),
    path('-declarations/delete/<int:pk>', views.fee_declaration_delete, name='fee_declaration_delete'),
     path('-get-semesters-by-course', get_semesters_by_course, name='get_semesters_by_course'),
     path('-tracker-&-collection', views.student_fee_list, name='student_fee_list'),
path('-optional-fee', views.optional_fee, name='optional_fee'),
path('-management', views.fee_dashboard, name='fee_dashboard'),
path('-collect-fee', views.fee_collection_collect, name='fee_collection_collect'),
    path('-collect-fee-payment', views.collect_fee_payment_page, name='collect_fee_payment_page'),
    path('-generate-qr', views.generate_qr_dynamic, name='generate_qr_dynamic'),
     
       re_path(r'^/receipt/(?P<admission_no>.+)/$', generate_receipt, name='generate_receipt'),



]