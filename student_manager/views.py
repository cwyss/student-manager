"""Views"""

import csv, re
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from student_manager import forms, models


class ImportExercisesView(FormView):
    template_name = 'student_manager/import_ex.html'
    form_class = forms.ImportExercisesForm

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
                    sheet += 1
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
        if points.strip()=='':
            return
        try:
            exercise = models.Exercise.objects.get(student=student, sheet=sheet)
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


class ImportStudentsView(FormView):
    template_name = 'student_manager/import_stud.html'
    form_class = forms.ImportStudentsForm

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
                                     last_name=row[1].decode('UTF-8'),
                                     first_name=row[2].decode('UTF-8'),
                                     subject=row[3].decode('UTF-8'),
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


print_students_opt = FormView.as_view(
    template_name='student_manager/print_students_opt.html',
    form_class=forms.PrintStudentsOptForm)


class PrintStudentsView(ListView):
    template_name = 'student_manager/student_list.html'

    def get_queryset(self):
        total_exercises = models.Exercise.total_num_exercises()

        if self.request.GET.get('matrikel'):
            students = models.Student.objects.exclude(matrikel=None)
            students = students.order_by('modulo_matrikel',
                                         'obscured_matrikel')
        else:
            students = models.Student.objects.filter(matrikel=None)
            students = students.order_by('last_name', 'first_name')

        student_data = []

        for student in list(students):
            if not student.exercise_set.all():
                continue
            student.exercises = [None] * total_exercises
            for exercise in student.exercise_set.all():
                student.exercises[exercise.sheet-1] = exercise
            student_data.append(student)

        return student_data

print_students = PrintStudentsView.as_view()


class ImportExamsView(FormView):
    template_name = 'student_manager/import_exam.html'
    form_class = forms.ImportExamsForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        file = form.cleaned_data['file']
        self.examnr = form.cleaned_data['examnr']
        self.stats = {'newstud': [],
                      'new': [],
                      'updated': [],
                      'unchanged': [],
                      'error': []
                      }
        self.subjectcnt = 0
        self.linebuf = []
        self.columns = None
        self.subject = None
        for line in file:
            line = line.decode('UTF-8')
            self.examine_line(line)
            self.process_lines()
        self.process_lines(final=True)

        messages.info(
            self.request,
            '%d exam entries with %d subjects processed.' % 
            (sum(map(len, self.stats.itervalues())),
             self.subjectcnt))
        if self.stats['newstud']:
            messages.success(
                self.request,
                '%d new students.' % len(self.stats['newstud']))
        if self.stats['new']:
            messages.success(
                self.request,
                '%d new exams.' % len(self.stats['new']))
        if self.stats['updated']:
            messages.success(
                self.request,
                '%d exams updated.' % len(self.stats['updated']))
        if self.stats['error']:
            for line in self.stats['error'][:10]:
                messages.warning(
                    self.request,
                    'Format error line: %s' % line)
        return super(ImportExamsView, self).form_valid(form)

    def examine_line(self, line):
        if line.startswith('subject:'):
            if len(self.linebuf)>0:
                self.stats['error'].extend(self.linebuf)
                self.linebuf = []
            self.columns = None
            self.subject = line[8:].strip()
            self.subjectcnt += 1
            return
        cols = self.find_columns(line)
        if cols:
            if not self.columns:
                self.columns = cols
                self.linebuf.append(line)
            elif self.columns!=cols:
                self.stats['error'].append(line)
            else:
                self.linebuf.append(line)
        elif line.isspace():
            if len(self.linebuf)>0:
                self.stats['error'].extend(self.linebuf)
                self.linebuf = []
            self.columns = None
        else:
            self.linebuf.append(line)

    def find_columns(self, line):
        m = re.match(r"\s*(\d+) (.+?) (\d+) (\d)", line, re.U)
        if not m:
            return None
        m2 = re.match(r"(.+?)  \s*(\S.+?)", m.group(2), re.U)
        if not m2:
            m2 = re.match(r"(\S+?) (\S+?)\s*\Z", m.group(2), re.U)
        if not m2:
            return None
        return (m.start(2), m.start(2)+m2.start(2), m.end(3)-7, m.start(4))

    def process_lines(self, final=False):
        if self.columns:
            for line in self.linebuf:
                self.save_exam(line, self.columns)
            self.linebuf = []
        elif final and len(self.linebuf)>0:
            self.stats['error'].extend(self.linebuf)
            self.linebuf = []

    def save_exam(self, line, cols):
#        nr = int(line[:cols[0]])
        try:
            name = line[cols[0]:cols[1]].strip()
            first_name = line[cols[1]:cols[2]].strip()
            matr = int(line[cols[2]:cols[3]])
            resit = int(line[cols[3]])
        except (IndexError, ValueError):
            self.stats['error'].append(line)
            return
        try:
            student = models.Student.objects.get(matrikel=matr)
        except models.Student.DoesNotExist:
            student = models.Student(matrikel=matr,
                                     last_name=name,
                                     first_name=first_name)
            student.save()
            status = 'newstud'
        else:
            status = 'new'
        try:
            exam = models.Exam.objects.get(student=student, examnr=self.examnr)
            if exam.subject==self.subject and exam.resit==resit:
                status = 'unchanged'
            else:
                status = 'updated'
        except models.Exam.DoesNotExist:
            exam = models.Exam(student=student, 
                               examnr=self.examnr)
        exam.subject = self.subject
        exam.resit = resit
        exam.save()
        self.stats[status].append(line)
                    
import_exams = staff_member_required(ImportExamsView.as_view())


print_exams_opt = FormView.as_view(
    template_name='student_manager/print_exams_opt.html',
    form_class=forms.PrintExamsOptForm)


class PrintExamsView(ListView):
    template_name = 'student_manager/exam_list.html'

    def get_queryset(self):
        examnr = int(self.request.GET.get('examnr'))

        exams = models.Exam.objects.filter(examnr=examnr)
        exams = exams.order_by('student__modulo_matrikel',
                               'student__obscured_matrikel')
        return list(exams)


print_exams = PrintExamsView.as_view()
