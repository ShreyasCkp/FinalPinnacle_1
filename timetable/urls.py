from django.urls import path
from . import views



urlpatterns = [
    
    path('class-timetable', views.timetable_dashboard, name='timetable_dashboard'),

   path('daily-timetable', views.daily_timetable, name='daily_timetable'),

    path('weekly/<int:course_id>/<int:semester_number>', views.weekly_timetable_view, name='weekly_timetable'),
    # path('faculty/<int:faculty_id>/', views.faculty_timetable_view, name='faculty_timetable'),
   
     path('<int:course_id>/<int:semester_number>/weekly', views.weekly_timetable_view, name='weekly_timetable'),
     path('get-faculty', views.get_faculty_by_subject, name='get_faculty_by_subject'),
    path('add-timetable', views.timetable_form_add, name='timetable_form_add'),
  
   path('timetable-entry/edit/<int:entry_id>', views.timetable_form_edit, name='timetable_form_edit'),
   path('timetable-entrye/delete/<int:substitution_id>', views.timetable_form_delete, name='timetable_form_delete'),
     path('timetable-entry/view/<int:entry_id>', views.timetable_form_view, name='timetable_form_view'),
    path('faculty-schedule-overview', views.faculty_classes_table, name='faculty_classes_table'),

     # path('timetable/edit/<int:entry_id>/', views.edit_timetable_entry, name='edit_timetable_entry'),
    path('ajax/get-semesters-by-course',  views.get_semesters_by_course, name='get_semesters_by_course'),
    path('get-courses-by-program-type-and-batch/', views.get_courses_and_years_by_program_type, name='get_courses_and_years_by_program_type'),


]

