"""The admin page."""

from django.contrib import admin
from django.db.models import Count
from django import forms
from django.utils.translation import ugettext_lazy as _

from student_manager.models import Student, Exercise, validate_matrikel


class ExercisesCompleteListFilter(admin.SimpleListFilter):
    title = _('exercises')
    parameter_name = 'points'

    def lookups(self, request, model_admin):
        return (('complete', _('Exercises complete')),
                ('incomplete', _('Exercises incomplete')))

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        total = Exercise.total_num_exercises()
        # find students who have completed all exercises:
        query = Exercise.objects.values('student').annotate(
            count=Count('student')).order_by().filter(count=total)
        completed_student_ids = [i['student'] for i in query]

        if self.value() == 'incomplete':
            return queryset.exclude(id__in=completed_student_ids)
        if self.value() == 'complete':
            return queryset.filter(id__in=completed_student_ids)


class StudentForm(forms.ModelForm):

    class Meta:
        model = Student

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        validate_matrikel(matrikel, student_id)
        return matrikel

        
class StudentAdmin(admin.ModelAdmin):
    list_display = ('matrikel', 'last_name', 'first_name',
                    'subject', 'semester', 'group', 'active',
                    'number_of_exercises', 'total_points', 'bonus')
    list_filter = (ExercisesCompleteListFilter, 'active', 'group')
    search_fields = ('matrikel', 'last_name', 'first_name')
    form = StudentForm


class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('sheet', 'points', 'group', 'student')
    list_filter = ('sheet', 'group')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')


admin.site.register(Student, StudentAdmin)
admin.site.register(Exercise, ExerciseAdmin)
