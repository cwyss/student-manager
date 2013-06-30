from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url='admin/')),
    url(r'^print/$', 'student_manager.views.print_students',
        name='print_students'),
    url(r'^import/$', 'student_manager.views.import_exercises',
        name='import_exercises'),
    url(r'^admin/', include(admin.site.urls)),
)
