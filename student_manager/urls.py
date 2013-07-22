from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='admin/')),
    url(r'^print_opts/$', 'student_manager.views.print_students_opt',
        name='print_students_opt'),
    url(r'^print/$', 'student_manager.views.print_students',
        name='print_students'),
    url(r'^import_exercises/$', 'student_manager.views.import_exercises',
        name='import_exercises'),
    url(r'^import_students/$', 'student_manager.views.import_students',
        name='import_students'),
    url(r'^import_exams/$', 'student_manager.views.import_exams',
        name='import_exams'),
    url(r'^admin/', include(admin.site.urls)),
)
