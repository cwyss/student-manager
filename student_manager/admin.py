"""The admin page."""

from django.contrib import admin
from django.db.models import Count
from django import forms
from django.utils.translation import ugettext_lazy as _

from student_manager.models import Student, Exercise, Exam, validate_matrikel


class NonuniqueModuloMatrikelListFilter(admin.SimpleListFilter):
    title = _('modulo matrikel')
    parameter_name = 'modulo_matrikel'

    def lookups(self, request, model_admin):
        return (('nonunique', _('With non-unique modulo matrikel')),)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        if self.value() == 'nonunique':
            duplicates = Student.objects.values('modulo_matrikel')
            duplicates = duplicates.annotate(Count('id'))
            duplicates = duplicates.values('modulo_matrikel').order_by()
            duplicates = duplicates.filter(id__count__gt=1)
            return queryset.filter(modulo_matrikel__in=duplicates)

class StudentForm(forms.ModelForm):

    class Meta:
        model = Student
        exclude = ('modulo_matrikel',)

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        validate_matrikel(matrikel, student_id)
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


class ExamAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'subject', 'resit', 'points')
    list_filter = ('exam', 'subject')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')


admin.site.register(Student, StudentAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Exam, ExamAdmin)
