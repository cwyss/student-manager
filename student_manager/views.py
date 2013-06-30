"""Views"""

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from student_manager import models


class ImportForm(forms.Form):
    group = forms.IntegerField()
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))


class ImportExercisesView(FormView):
    template_name = 'student_manager/import.html'
    form_class = ImportForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        # TODO: save csv file data here
        print form.cleaned_data['csv_file'].read()
        messages.success(self.request, '0 from 0 exercises imported.')
        return super(ImportExercisesView, self).form_valid(form)

import_exercises = staff_member_required(ImportExercisesView.as_view())


print_students = ListView.as_view(
    model=models.Student,
    queryset=models.Student.objects.order_by('matrikel'))
