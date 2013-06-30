"""Views"""

import csv

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
        group = form.cleaned_data['group']
        csvreader = csv.reader(
            form.cleaned_data['csv_file'],
            delimiter=str(form.cleaned_data['column_separator']))
        success = 0
        notfound = []
        for row in csvreader:
            try:
                student = models.Student.objects.get(matrikel=row[0])
            except models.Student.DoesNotExist:
                notfound.append(row[0])
                continue
            try:
                exercise = models.Exercise.objects.get(
                    student=student, number=row[1])
            except models.Exercise.DoesNotExist:
                exercise = models.Exercise(student=student, number=row[1])
            exercise.points = row[2]
            exercise.group = group
            exercise.save()
            success += 1
        if notfound:
            messages.warning(
                self.request,
                '%s exercises imported, %s unknown students ignored: %s' % (
                    success, len(notfound), ', '.join(notfound)))
        else:
            messages.success(self.request, '%s exercises imported.' % success)
        return super(ImportExercisesView, self).form_valid(form)

import_exercises = staff_member_required(ImportExercisesView.as_view())


print_students = ListView.as_view(
    model=models.Student,
    queryset=models.Student.objects.order_by('matrikel'))
