from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='admin/', permanent=True)),
    url(r'^print_exercises_opt/$', 'student_manager.views.print_exercises_opt',
        name='print_exercises_opt'),
    url(r'^print_exercises/$', 'student_manager.views.print_exercises',
        name='print_exercises'),
    url(r'^print_exsheet_opt/$', 'student_manager.views.print_exsheet_opt',
        name='print_exsheet_opt'),
    url(r'^print_exsheet/$', 'student_manager.views.print_exsheet',
        name='print_exsheet'),
    url(r'^print_students_opt/$', 'student_manager.views.print_students_opt',
        name='print_students_opt'),
    url(r'^print_students/$', 'student_manager.views.print_students',
        name='print_students'),
    url(r'^print_groups_opt/$', 'student_manager.views.print_groups_opt',
        name='print_groups_opt'),
    url(r'^print_groups/$', 'student_manager.views.print_groups',
        name='print_groups'),
    url(r'^print_exams_opt/$', 'student_manager.views.print_exams_opt',
        name='print_exams_opt'),
    url(r'^print_exams/$', 'student_manager.views.print_exams',
        name='print_exams'),
    url(r'^import_exercises/$', 'student_manager.views.import_exercises',
        name='import_exercises'),
    url(r'^import_students/$', 'student_manager.views.import_students',
        name='import_students'),
    url(r'^import_registrations/$',
        'student_manager.views.import_registrations',
        name='import_registrations'),
    url(r'^import_exams/$', 'student_manager.views.import_exams',
        name='import_exams'),
    url(r'^import_entrytests/$', 'student_manager.views.import_entrytests',
        name='import_entrytests'),
    url(r'^save_exam_results/$', 'student_manager.views.save_exam_results',
        name='save_exam_results'),
    url(r'^save_exercise_results/$',
        'student_manager.views.save_exercise_results',
        name='save_exercise_results'),
    url(r'^query_students_opt/$', 'student_manager.views.query_students_opt',
        name='query_students_opt'),
    url(r'^query_students/$', 'student_manager.views.query_students',
        name='query_students'),
    url(r'^query_exams_opt/$', 'student_manager.views.query_exams_opt',
        name='query_exams_opt'),
    url(r'^query_exams/$', 'student_manager.views.query_exams',
        name='query_exams'),
    url(r'^query_regist/$', 'student_manager.views.query_regist',
        name='query_regist'),
    url(r'^query_new_assigned/$',
        'student_manager.views.query_new_assigned',
        name='query_new_assigned'),
    url(r'^query_exercise/$',
        'student_manager.views.query_exercise',
        name='query_exercise'),
    url(r'^export_students/$', 'student_manager.views.export_students',
        name='export_students'),
    url(r'^query_examparts_opt/$', 'student_manager.views.query_examparts_opt',
        name='query_examparts_opt'),
    url(r'^query_examparts/$', 'student_manager.views.query_examparts',
        name='query_examparts'),
    url(r'^query_special_opt/$', 'student_manager.views.query_special_opt',
        name='query_special_opt'),
    url(r'^query_special/$', 'student_manager.views.query_special',
        name='query_special'),
    url(r'^admin/', include(admin.site.urls)),
)
