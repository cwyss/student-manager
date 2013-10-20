from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='admin/')),
    url(r'^print_students_opt/$', 'student_manager.views.print_students_opt',
        name='print_students_opt'),
    url(r'^print_students/$', 'student_manager.views.print_students',
        name='print_students'),
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
    url(r'^save_exam_results/$', 'student_manager.views.save_exam_results',
        name='save_exam_results'),
    url(r'^query_exams_opt/$', 'student_manager.views.query_exams_opt',
        name='query_exams_opt'),
    url(r'^query_exams/$', 'student_manager.views.query_exams',
        name='query_exams'),
    url(r'^query_regist/$', 'student_manager.views.query_regist',
        name='query_regist'),
    url(r'^query_assigned_group/$', 
        'student_manager.views.query_assigned_group',
        name='query_assigned_group'),
    url(r'^admin/', include(admin.site.urls)),
)
