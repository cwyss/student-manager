"""Views"""

import csv
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from student_manager import models


class ImportExercisesForm(forms.Form):
    group = forms.IntegerField()
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))
    format = forms.ChoiceField(choices=(
            ('', 'Please select'),
            (1, 'Exercise table (one entry per exercise)'),
            (2, 'Big table (one column per sheet)')))


class ImportExercisesView(FormView):
    template_name = 'student_manager/import_ex.html'
    form_class = ImportExercisesForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        group = form.cleaned_data['group']
        csvreader = csv.reader(
            form.cleaned_data['csv_file'],
            delimiter=str(form.cleaned_data['column_separator']))
        self.stats = {'new': [],
                      'updated': [],
                      'unchanged': [],
                      'unknown_student': [],
                      'invalid_points': []}
        for line, row in enumerate(csvreader):
            if line == 0 and not row[0].isdigit():
                # We seem to have a header; ignore.
                continue
            try:
                student = models.Student.objects.get(matrikel=row[0])
            except models.Student.DoesNotExist:
                self.stats['unknown_student'].append(row[0])
                continue
            if form.cleaned_data['format'] == '1':
                self.save_exercise(group, student, row[1], row[2])
            elif form.cleaned_data['format'] == '2':
                for sheet, points in enumerate(row[1:]):
                    self.save_exercise(group, student, sheet, points)
            else:
                raise ValueError('Unknown format.')

        messages.info(
            self.request,
            '%s entries processed.' % sum(map(len, self.stats.itervalues())))
        if self.stats['new']:
            messages.success(
                self.request,
                '%s new exercises created.' % len(self.stats['new']))
        if self.stats['updated']:
            messages.success(
                self.request,
                '%s exercises updated.' % len(self.stats['updated']))
        if self.stats['unknown_student']:
            ustudset = set(self.stats['unknown_student'])
            messages.warning(
                self.request,
                '%s unknown students: %s' % (len(ustudset),
                                             ', '.join(ustudset)))
        if self.stats['invalid_points']:
            invpset = set(self.stats['invalid_points'])
            messages.warning(
                self.request,
                '%s invalid points: %s' % (len(invpset),
                                           ', '.join(invpset)))
        
        return super(ImportExercisesView, self).form_valid(form)

    def save_exercise(self, group, student, sheet, points):
        try:
            exercise = models.Exercise.objects.get(
                student=student, sheet=sheet)
#            print repr(points), repr(exercise.points)
            if exercise.points==Decimal(points):
                status = 'unchanged'
            else:
                status = 'updated'
        except models.Exercise.DoesNotExist:
            exercise = models.Exercise(student=student, sheet=sheet)
            status = 'new'
        exercise.points = points
        exercise.group = group
        try:
            exercise.save()
        except ValidationError:
            status = 'invalid_points'

        self.stats[status].append(str(student.matrikel))
                    
import_exercises = staff_member_required(ImportExercisesView.as_view())


class ImportStudentsForm(forms.Form):
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))


class ImportStudentsView(FormView):
    template_name = 'student_manager/import_stud.html'
    form_class = ImportStudentsForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        csvreader = csv.reader(
            form.cleaned_data['csv_file'],
            delimiter=str(form.cleaned_data['column_separator']))

        self.stats = {'new': [],
                      'exists': [],
                      'nomatr': []
                      }
        for line, row in enumerate(csvreader):
            if line == 0 and not row[0].isdigit():
                # We seem to have a header; ignore.
                continue

            if row[0].isdigit():
                matrikel = row[0]
                status = 'new'
            else:
                matrikel = None
                status = 'nomatr'
            if row[4].isdigit():
                semester = row[4]
            else:
                semester = None
            if row[5].isdigit():
                group = row[5]
            else:
                group = None
            student = models.Student(matrikel=matrikel,
                                     last_name=row[1].decode('latin-1'),
                                     first_name=row[2].decode('latin-1'),
                                     subject=row[3].decode('latin-1'),
                                     semester=semester,
                                     group=group)
            try:
                student.save()
            except ValidationError:
                status = 'exists'
            self.stats[status].append(student.matrikel)

        messages.info(
            self.request,
            '%s entries processed.' % sum(map(len, self.stats.itervalues())))
        if self.stats['new']:
            messages.success(
                self.request,
                '%s new students (with matrikel) created.' \
                    % len(self.stats['new']))
        if self.stats['nomatr']:
            messages.success(
                self.request,
                '%s students without matrikel created.' \
                    % len(self.stats['nomatr']))
        if self.stats['exists']:
            messages.warning(
                self.request,
                '%s matrikel numbers already exist: %s' \
                    % (len(self.stats['exists']),
                       ', '.join(self.stats['exists'])))

        return super(ImportStudentsView, self).form_valid(form)

import_students = staff_member_required(ImportStudentsView.as_view())


class PrintStudentsOptForm(forms.Form):
    matrikel = forms.ChoiceField(label=_('Selection'),
                                 choices=(('', 'Students without matrikel'),
                                         ('on', 'Students with matrikel')))
    total = forms.BooleanField(label=_('Display total/bonus columns'))

print_students_opt = FormView.as_view(
    template_name='student_manager/print_students_opt.html',
    form_class=PrintStudentsOptForm)


class PrintStudentsView(ListView):
    template_name = 'student_manager/student_list.html'

    def get_queryset(self):
        total_exercises = models.Exercise.total_num_exercises()
        if self.request.GET.get('matrikel'):
            students = list(models.Student.objects.exclude(matrikel=None))
        else:
             students = list(models.Student.objects.filter(matrikel=None))
           
        for student in students:
            if self.request.GET.get('matrikel'):
                student.identifier = str(student.matrikel)[-4:]
                student.sort = str(student.matrikel)[-4:]
            else:
                student.identifier = '%s, %s' % (student.last_name,
                                                 student.first_name)
                student.sort = (student.last_name, student.first_name)
            student.exercises = [None] * total_exercises
            for exercise in student.exercise_set.all():
                student.exercises[exercise.sheet-1] = exercise

        students.sort(key=lambda s: s.sort)
        return students

print_students = PrintStudentsView.as_view()

