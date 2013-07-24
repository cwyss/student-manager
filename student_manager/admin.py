"""The admin page."""

from django.contrib import admin
from django.contrib import messages
from django.db.models import Count
from django import forms
from django.utils.translation import ugettext_lazy as _

from student_manager import models


class NonuniqueModuloMatrikelListFilter(admin.SimpleListFilter):
    title = _('modulo matrikel')
    parameter_name = 'modulo_matrikel'

    def lookups(self, request, model_admin):
        return (('nonunique', _('With non-unique modulo matrikel')),)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        if self.value() == 'nonunique':
            duplicates = models.Student.objects.values('modulo_matrikel')
            duplicates = duplicates.annotate(Count('id'))
            duplicates = duplicates.values('modulo_matrikel').order_by()
            duplicates = duplicates.filter(id__count__gt=1)
            return queryset.filter(modulo_matrikel__in=duplicates)

class StudentForm(forms.ModelForm):

    class Meta:
        model = models.Student
        exclude = ('modulo_matrikel',)

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        models.validate_matrikel(matrikel, student_id)
        return matrikel

        
class StudentAdmin(admin.ModelAdmin):
    list_display = ('matrikel', 'modulo_matrikel', 'obscured_matrikel',
                    'last_name', 'first_name', 'subject', 'semester',
                    'group', 'active', 'number_of_exercises', 'total_points',
                    'bonus')
    list_filter = (NonuniqueModuloMatrikelListFilter, 'active', 'group')
    search_fields = ('matrikel', 'last_name', 'first_name')
    form = StudentForm


class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('sheet', 'points', 'group', 'student')
    list_filter = ('sheet', 'group')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')


class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'examnr', 'capacity', 'priority')
    list_filter = ('examnr',)


def assign_seats(modeladmin, request, queryset):
    examnr = queryset[0].examnr
    if queryset.exclude(examnr=examnr).exists():
        messages.error(request, 'Selection contains different exam numbers.')
        return
    rooms = models.Room.objects.filter(examnr=examnr).order_by('priority')
    roomlist = []
    maxnumber = 0
    for room in rooms:
        if room.capacity is None:
             messages.error(request, 'Room %s has no capacity' % room)
             return
        maxnumber += room.capacity
        roomlist.append((maxnumber, room))
         
    if maxnumber <= 0:
        messages.error(request,
                       'No rooms with capacity found for exam %s' % examnr)
        return
    
    queryset.update(number=None)
    roomdata = roomlist.pop(0)
    for i, exam in enumerate(queryset):
        if i >= roomdata[0] and roomlist:
            roomdata = roomlist.pop(0)
        exam.number = i+1
        exam.room = roomdata[1]
        exam.save()
    messages.success(request, 'Assigned %s seats' % queryset.count())


class ExamAdmin(admin.ModelAdmin):
    list_display = ('examnr', 'student', 'subject', 'number', 
                    'room', 'resit', 'points', )
    list_filter = ('examnr', 'subject', 'room')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')
    actions = (assign_seats,)


admin.site.register(models.Student, StudentAdmin)
admin.site.register(models.Exercise, ExerciseAdmin)
admin.site.register(models.Room, RoomAdmin)
admin.site.register(models.Exam, ExamAdmin)
