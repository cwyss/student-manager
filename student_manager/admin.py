"""The admin page."""

from collections import defaultdict

from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _

from student_manager.models import Student, Exercise, validate_matrikel


class NonuniqueObscuredMatrikelListFilter(admin.SimpleListFilter):
    title = _('obscured matrikel')
    parameter_name = 'obscured_matrikel'

    def lookups(self, request, model_admin):
        return (('nonunique', _('With non-unique obscured matrikel')),)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        if self.value() == 'nonunique':
            matrikels = Student.objects.values_list('id', 'matrikel')
            short_matrikels = defaultdict(lambda: [])
            duplicates = []
            for (id_, matr) in matrikels:
                short_matr = str(matr)[-4:]
                if short_matr in short_matrikels:
                    duplicates.extend(short_matrikels[short_matr])
                    duplicates.append(id_)
                short_matrikels[short_matr].append(id_)
            return queryset.filter(id__in=duplicates)

class StudentForm(forms.ModelForm):

    class Meta:
        model = Student

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        validate_matrikel(matrikel, student_id)
        return matrikel

        
class StudentAdmin(admin.ModelAdmin):
    list_display = ('matrikel', 'obscured_matrikel', 'last_name', 'first_name',
                    'subject', 'semester', 'group', 'active',
                    'number_of_exercises', 'total_points', 'bonus')
    list_filter = (NonuniqueObscuredMatrikelListFilter, 'active', 'group')
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
