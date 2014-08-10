"""Views"""

import csv, re, json, urllib
import xml.etree.ElementTree as ElementTree
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Max, Count, F
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.views.generic import TemplateView

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
                      'invalid_points': [],
                      'no_matrikel': []}
        for line, row in enumerate(csvreader):
            if not row:
                # ignore empty line
                continue
            if not row[0].isdigit():
                if line == 0:
                    # We seem to have a header; ignore.
                    pass
                else:
                    self.stats['no_matrikel'].append(row)
                continue
            try:
                student = models.Student.objects.get(matrikel=row[0])
            except models.Student.DoesNotExist:
                self.stats['unknown_student'].append(row[0])
                continue
            if form.cleaned_data['format'] == 'exerc':
                self.save_exercise(group, student, row[1], row[2])
            elif form.cleaned_data['format'] == 'sheet':
                for i, points in enumerate(row[1:]):
                    sheet = i+1
                    self.save_exercise(group, student, sheet, points)

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
                '%s exercises updated: %s' % (len(self.stats['updated']),
                                              ', '.join(self.stats['updated'])))
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
        if self.stats['no_matrikel']:
            messages.warning(
                self.request,
                '%s entries without matrikel skipped.' \
                    % len(self.stats['no_matrikel']))

        return super(ImportExercisesView, self).form_valid(form)

    def save_exercise(self, group, student, sheet, points):
        status_msg = str(student.matrikel)
        if points.strip()=='':
            return
        points = points.replace(',', '.')
        try:
            exercise = models.Exercise.objects.get(student=student, sheet=sheet)
            if exercise.points==Decimal(points):
                status = 'unchanged'
            else:
                status = 'updated'
                status_msg += ", %d: %s->%s" % (sheet, exercise.points, points)
        except models.Exercise.DoesNotExist:
            exercise = models.Exercise(student=student, sheet=sheet)
            status = 'new'
        exercise.points = points
        exercise.group = group
        try:
            exercise.save()
        except ValidationError:
            self.stats['invalid_points'].append(status_msg)
            return
        
        if student.group==None:
            student.group = group
            student.save()

        self.stats[status].append(status_msg)

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
                group = models.Group.get_group(int(row[5]), create=True)
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


print_groups_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/print_groups_opt.html',
    form_class=forms.PrintGroupsOptForm))


class PrintGroupsView(ListView):
    template_name = 'student_manager/group_list.html'

    def get_queryset(self):
        students = models.Student.objects.exclude(group=None)
        if self.request.GET.get('matrikel'):
            students = students.exclude(matrikel=None)
            students = students.order_by('matrikel')
        else:
            students = students.filter(matrikel=None)
            students = students.order_by('last_name', 'first_name')
        return students

print_groups = staff_member_required(PrintGroupsView.as_view())


print_exercises_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/print_exercises_opt.html',
    form_class=forms.PrintExercisesOptForm))


class PrintExercisesView(ListView):
    template_name = 'student_manager/exercise_list.html'

    def get_queryset(self):
        total_exercises = models.Exercise.total_num_exercises()
        selection = self.request.GET.get('selection')
        group = self.request.GET.get('group')
        exclude = self.request.GET.get('exclude')
        total = self.request.GET.get('total')
        try:
            maxpoints = float(models.StaticData.objects.get(
                    key='maxpoints').value)
        except models.StaticData.DoesNotExist:
            maxpoints = None

        students = models.Student.objects.exclude(group=None)
        # exclude students coming only from exam entries

        if selection=='matrikel':
            students = students.exclude(matrikel=None)
            students = students.order_by('modulo_matrikel',
                                         'obscured_matrikel')
        elif selection=='nomatrikel':
            students = students.filter(matrikel=None)
            students = students.order_by('last_name', 'first_name')
        else:
            if group:
                students = students.filter(group=group)
            students = students.order_by('last_name', 'first_name')

        if exclude=='inactive':
            students = students.filter(active=True)

        student_data = []

        for student in list(students):
            if exclude=='empty' and not student.exercise_set.all():
                continue
            student.exercises = [None] * total_exercises
            for exercise in student.exercise_set.all():
                student.exercises[exercise.sheet-1] = exercise
            if total:
                if maxpoints:
                    student.percent = float(student.total_points()) \
                        / maxpoints * 100
                else:
                    student.percent = None
            student_data.append(student)

        return student_data

    def get_context_data(self, **kwargs):
        context = super(PrintExercisesView, self).get_context_data(**kwargs)
        selection = self.request.GET.get('selection')
        if selection=='matrikel':
            context['matrikel'] = True
        else:
            context['matrikel'] = False
        return context

print_exercises = staff_member_required(PrintExercisesView.as_view())


print_students_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/print_students_opt.html',
    form_class=forms.PrintStudentsOptForm))


class PrintStudentsView(ListView):
    template_name = 'student_manager/student_list.html'

    def get_queryset(self):
        if self.request.GET.get('order_by')=='matrikel':
            students = models.Student.objects.order_by('matrikel')
        else:
            students = models.Student.objects.order_by(
                'last_name', 'first_name')
        return students

print_students = staff_member_required(PrintStudentsView.as_view())


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
        self.subject = None
        for line in file:
            line = line.decode('UTF-8')
            cols = self.examine_line(line)
            if cols:
                self.save_exam(line, cols)

        messages.info(
            self.request,
            '%d exam entries with %d subjects processed.' %
            (sum(map(len, self.stats.itervalues())),
             self.subjectcnt))
        if self.stats['newstud']:
            messages.success(
                self.request,
                '%d new exams with new students.' % len(self.stats['newstud']))
        if self.stats['new']:
            messages.success(
                self.request,
                '%d new exams with known students.' % len(self.stats['new']))
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
            self.subject = line[8:].strip()
            self.subjectcnt += 1
            return None
        elif line.isspace():
            return None
        cols = self.find_columns(line)
        if cols:
            return cols
        else:
            self.stats['error'].append(line)
            return None

    def find_columns(self, line):
        m = re.match(r"\s*(\d+) (.+?) (\d+)\s+(\d)", line, re.U)
        if not m:
            return None
        m2 = re.match(r"\s*(\S.+?)  \s*(\S.+)", m.group(2), re.U)
        if not m2:
            m2 = re.match(r"\s*(\S+?) (\S+?)\s*\Z", m.group(2), re.U)
        if not m2:
            return None
        return (m.start(2), m.start(2)+m2.start(2), m.end(3)-7, m.start(4))

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
                                     first_name=first_name,
                                     subject=self.subject)
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


print_exams_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/print_exams_opt.html',
    form_class=forms.PrintExamsOptForm))


class PrintExamsView(ListView):
    def get_queryset(self):
        examnr = self.request.GET.get('examnr')
        format = self.request.GET.get('format')
        exams = models.Exam.objects.filter(examnr=examnr)
        if format.endswith('obscured'):
            exams = exams.order_by('student__modulo_matrikel',
                                   'student__obscured_matrikel')
            if format == 'exam_obscured':
                self.template_name = 'student_manager/exam_list.html'
            else:
                exams = exams.exclude(points=None)
                self.template_name = 'student_manager/result_list.html'
        elif format == 'exam_full':
            exams = exams.order_by('number')
            self.template_name = 'student_manager/exam_full_list.html'
        else:
            exams = exams.order_by('student__last_name',
                                   'student__first_name')
            self.template_name = 'student_manager/result_full_list.html'
        return list(exams)

    def get_context_data(self, **kwargs):
        context = super(PrintExamsView, self).get_context_data(**kwargs)
        examnr = self.request.GET.get('examnr')
        masterexam = models.MasterExam.objects.get(id=examnr)
        context['examtitle'] = masterexam.title
        context['max_points'] = masterexam.max_points
        mark_ranges = []
        if masterexam.mark_limits:
            mark_limits = json.loads(masterexam.mark_limits)
            entry = mark_limits[0]
            mark_ranges.append((masterexam.max_points,
                                entry[0], entry[1]))
            last_limit = entry[0]
            for entry in mark_limits[1:]:
                mark_ranges.append((last_limit-.5, entry[0], entry[1]))
                last_limit = entry[0]
                if entry[1] == 4.0:
                    context['pass_points'] = entry[0]
        context['mark_ranges'] = mark_ranges
        return context

print_exams = staff_member_required(PrintExamsView.as_view())


@staff_member_required
@require_POST
def save_exam_results(request, queryset=None):
    if queryset is not None:
        # initial form
        formset = forms.ExamFormSet(queryset=queryset)
        num_exercises = queryset.aggregate(
            max=Max('examnr__num_exercises'))['max']
        num_exercises_form = forms.NumberExercisesForm(
            initial={'num_exercises': num_exercises})
    else:
        # submitted form
        formset = forms.ExamFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Exam results updated.')
            return HttpResponseRedirect(
                reverse('admin:student_manager_exam_changelist') \
                    + '?' + urllib.urlencode(request.GET))
        num_exercises_form = forms.NumberExercisesForm(request.POST)
        if num_exercises_form.is_valid():
            num_exercises = num_exercises_form.cleaned_data['num_exercises']
        else:
            raise ValidationError('Can\'t determine number of exercises')

    return render_to_response(
        'student_manager/enter_exam_results.html',
        {'formset': formset,
         'num_exercises': range(1, num_exercises + 1),
         'num_exercises_form': num_exercises_form,
         'params': urllib.urlencode(request.GET)},
        context_instance=RequestContext(request))


query_exams_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/query_exams_opt.html',
    form_class=forms.QueryExamsOptForm))


class QueryExamsView(TemplateView):
    template_name = 'student_manager/query_exams.html'

    def get_context_data(self, **kwargs):
        context = super(QueryExamsView, self).get_context_data(**kwargs)
        examnr = self.request.GET.get('examnr')

        exams = models.Exam.objects.filter(examnr=examnr)
        markcounts = exams.values('mark').order_by('mark') \
            .annotate(count=Count('id'))
        context['markcounts'] = markcounts

        context['missing_count'] = exams.filter(points=None).count()
        examlist = exams.exclude(points=None)
        context.update(
            attend_count = examlist.count(),
            pass_count = examlist.filter(mark__lte=4.0).count(),
            fail_count = examlist.filter(mark=5.0).count()
            )

        context['pointgroups'] = self.get_pointgroups(examnr)
        return context

    def get_pointgroups(self, examnr):
        masterexam = models.MasterExam.objects.get(id=examnr)
        try:
            pointstep = int(models.StaticData.objects.get(
                    key='query_exam_pointstep').value)
        except models.StaticData.DoesNotExist:
            pointstep = 2

        examlist = models.Exam.objects.filter(examnr=examnr) \
            .exclude(points=None)
        pointcounts = examlist.values('points').order_by('points') \
            .annotate(count=Count('id'))

        group = {'lower': 0, 'upper': pointstep, 'count': 0}
        pointgroups = [group]
        for item in pointcounts:
            while item['points'] >= group['upper']:
                nextgroup = {'lower': group['upper'],
                             'upper': group['upper']+pointstep,
                             'count': 0}
                pointgroups.append(nextgroup)
                group = nextgroup
            group['count'] += item['count']
        if masterexam.max_points and group['upper'] > masterexam.max_points:
            del pointgroups[-1]
            pointgroups[-1]['count'] += group['count']
        return pointgroups


query_exams = staff_member_required(QueryExamsView.as_view())


query_students_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/query_students_opt.html',
    form_class=forms.QueryStudentsOptForm))


class QueryStudentsView(TemplateView):
    template_name = 'student_manager/generic_query.html'

    def get_context_data(self, **kwargs):
        context = super(QueryStudentsView, self).get_context_data(**kwargs)
        first_field = self.request.GET.get('first_field')
        second_field = self.request.GET.get('second_field')
        only_active = self.request.GET.get('only_active')

        """ cannot use
              qset = models.Student.object
            here, because of annotation with Exercise in Student model
            (class StudentManager) """
        qset = models.Student.objects.get_pure_query_set()
        if only_active:
            qset = qset.filter(active=True)
        context['first_field'] = first_field
        if second_field=='None':
            self.make_data1(qset, first_field, context)
        else:
            context['second_field'] = second_field
            self.make_data2(qset, first_field, second_field, context)
        return context

    def make_data1(self, qset, field, context):
        context['headline'] = [field, '&#8721;']
        if field=='group':
            field = 'group__number'
        qset = qset.values(field).order_by(field) \
            .annotate(count=Count('id'))
        data = []
        for agrp in qset:
            data.append((agrp[field], agrp['count']))
        context['data'] = data

    def make_data2(self, qset, field1, field2, context):
        context['headline'] = [field1]
        if field1=='group':
            field1 = 'group__number'
        if field2=='group':
            field2 = 'group__number'
        qf1 = qset.values(field1).order_by(field1) \
            .annotate(count=Count('id'))
        qf2 = qset.values(field2).order_by(field2) \
            .annotate(count=Count('id'))
        field2_dict = {}
        for (i,d) in enumerate(qf2):
            field2_dict[d[field2]] = i
            context['headline'].append(d[field2])
        context['headline'].append('&#8721;')

        context['data'] = []
        for df1 in qf1:
            line = [df1[field1]]
            qf = qset.filter(**{field1: df1[field1]}) \
                .values(field2).order_by(field2) \
                .annotate(count=Count('id'))
            counts = [0] * len(field2_dict)
            for d in qf:
                i = field2_dict[d[field2]]
                counts[i] = d['count']
            line.extend(counts)
            line.append(df1['count'])
            context['data'].append(line)

        counts = [d['count'] for d in qf2]
        context['bottomline'] = ['&#8721;'] + counts + [sum(counts)]

query_students = staff_member_required(QueryStudentsView.as_view())


class ImportRegistrationsView(FormView):
    template_name = 'student_manager/import_registration.html'
    form_class = forms.ImportRegistrationsForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        file = form.cleaned_data['file']
        column_sep = str(form.cleaned_data['csv_separator'])
        import_choice = str(form.cleaned_data['import_choice'])
        update_choice = str(form.cleaned_data['update_choice'])
        create_groups = form.cleaned_data['create_groups']

        self.stats = {'new': [],
                      'update': [],
                      'unchanged': [],
                      'nogroup': {},
                      'regist_new': 0,
                      'regist_update': 0,
                      'dupl_regist': [],
                      }
        self.worksheet_name = None
        self.groups = []
        self.student_dict = {}

        self.subject_translation = \
            models.StaticData.get_subject_transl()
        if not self.read_xls(file):
            self.read_csv(file, column_sep)
        self.group_translation = \
            models.Group.get_group_transl(self.groups, create=create_groups)
        self.import_data(import_choice, update_choice)

        if self.worksheet_name:
            messages.success(
                self.request,
                'Worksheet "%s" from xls file read.' % self.worksheet_name)
        else:
            messages.success(self.request, 'csv file read.')
        if self.stats['nogroup'] and \
                (import_choice!='none' or update_choice!='none'):
            nogrp_out = ['%s: %d' % x \
                             for x in self.stats['nogroup'].iteritems()]
            messages.warning(
                self.request,
                'No such group in translation: %s' \
                    % ', '.join(nogrp_out))
        if self.stats['dupl_regist']:
            dupl_out = ['%d: Grp %s' % (d[0],d[1])
                        for d in self.stats['dupl_regist']]
            messages.warning(
                self.request,
                'Duplicate registration: %s' % ', '.join(dupl_out))
        if import_choice in ('stud', 'all'):
            messages.success(
                self.request,
                'Student data for %d new students imported.' % \
                    len(self.stats['new']))
        if update_choice in ('stud', 'all'):
            messages.success(
                self.request,
                'Student data for %d existing students updated.' % \
                    len(self.stats['update']))
        if self.stats['regist_new']>0:
            messages.success(
                self.request,
                '%d registrations for %d new students added.'  % \
                    (self.stats['regist_new'],
                     len(self.stats['new'])))
        if self.stats['regist_update']>0:
            messages.success(
                self.request,
                '%d registrations for %d existing students added/updated.'  % \
                    (self.stats['regist_update'],
                     len(self.stats['update']) + len(self.stats['unchanged'])))
        return super(ImportRegistrationsView, self).form_valid(form)

    def transl_subj(self, subject):
        if type(subject)==unicode:
            subject = subject.translate({0xa0: 32})
        if  self.subject_translation.has_key(subject):
            return self.subject_translation[subject]
        else:
            return subject

    def add_registration(self, matrikel,
                         last_name, first_name,
                         subject, semester,
                         status, priority, group_str):
        matrikel = int(matrikel)
        if self.student_dict.has_key(matrikel):
            stud = self.student_dict[matrikel]
            if not stud[2]:
                stud[2] = self.transl_subj(subject)
            if not stud[3] and semester.isdigit():
                stud[3] = semester
        else:
            if not semester.isdigit():
                semester = None
            stud = [last_name, first_name,
                    self.transl_subj(subject),
                    semester,
                    []                    # registrations
                    ]
            self.student_dict[matrikel] = stud
        if type(group_str)==unicode:
            group_str = group_str.translate({0xa0: 32})
        if group_str not in self.groups:
            self.groups.append(group_str)
        if not priority.isdigit():
            priority = None
        stud[4].append((group_str, status, priority))

    def add_table(self, table):
        header = True
        for row in table:
            if len(row)==0:                    # ignore empty lines
                continue
            if header:
                if not row[0].isdigit():       # ignore header
                    continue
                else:
                    header = False
            self.add_registration(matrikel=row[0],
                                  last_name=row[1],
                                  first_name=row[2],
                                  subject=row[4],
                                  semester=row[6],
                                  status=row[7],
                                  priority=row[8],
                                  group_str=row[9])

    def read_csv(self, csv_file, column_sep):
        csvreader = csv.reader(csv_file, delimiter=column_sep)
        table = []
        for row in csvreader:
            table.append([c.decode('utf-8') for c in row])
        self.add_table(table)

    def read_xls(self, file):
        NSHEAD = '{urn:schemas-microsoft-com:office:spreadsheet}'
        tree = ElementTree.ElementTree()
        try:
            root = tree.parse(file)
        except ElementTree.ParseError:
            return False
        worksheet = root.find(NSHEAD+'Worksheet')
        self.worksheet_name = worksheet.attrib[NSHEAD+'Name']
        table_elem = worksheet.find(NSHEAD+'Table')
        table = []
        for row in table_elem:
            if row.tag!=NSHEAD+'Row':
                continue
            accu = []
            for cell in row:
                if cell.tag!=NSHEAD+'Cell':
                    continue
                data = cell.find(NSHEAD+'Data')
                if data.attrib[NSHEAD+'Type']=='String':
                    if data.text!=None:
                        accu.append(data.text)
                    else:
                        accu.append('')
            table.append(accu)
        self.add_table(table)
        return True

    def import_data(self, import_choice, update_choice):
        for matrikel, stud in self.student_dict.iteritems():
            try:
                student = models.Student.objects.get(matrikel=matrikel)
                if update_choice=='none':
                    continue
                state = 'unchanged'
                if update_choice in ('stud', 'all'):
                    if not student.last_name:
                        student.last_name = stud[0]
                        student.first_name = stud[1]
                        state = 'update'
                    if not student.subject:
                        student.subject = stud[2]
                        student.semester = stud[3]
                        state = 'update'
                    if state=='update':
                        student.save()
                if update_choice in ('regist', 'all'):
                    save_regist = True
                else:
                    save_regist = False
            except models.Student.DoesNotExist:
                if import_choice=='none':
                    continue
                state = 'new'
                student = models.Student(matrikel=matrikel,
                                         last_name=stud[0],
                                         first_name=stud[1],
                                         subject=stud[2],
                                         semester=stud[3])
                student.save()
                if import_choice=='all':
                    save_regist = True
                else:
                    save_regist = False
            self.stats[state].append(matrikel)

            if save_regist:
                # if state!='new':
                #     models.Registration.objects.filter(student=student).delete()
                models.Registration.objects.filter(student=student).delete()
                count = 0
                for regist in stud[4]:
                    try:
                        group = self.group_translation[regist[0]]
                    except KeyError:
                        self.stats['nogroup'][regist[0]] = matrikel
                        continue
                    registration = models.Registration(student=student,
                                                       group=group,
                                                       status=regist[1],
                                                       priority=regist[2])
                    try:
                        registration.save()
                    except IntegrityError:
                        self.stats['dupl_regist'].append((matrikel,
                                                          regist[0]))
                        continue
                    count += 1
                if state=='new':
                    self.stats['regist_new'] += count
                else:
                    self.stats['regist_update'] += count


import_registrations = staff_member_required(ImportRegistrationsView.as_view())


class QueryRegistrationsView(TemplateView):
    template_name = 'student_manager/query_regist.html'

    def get_context_data(self, **kwargs):
        context = super(QueryRegistrationsView, self).get_context_data(**kwargs)

        groups = models.Group.objects.order_by('number')
        context['groups'] = groups
        groupmap = self.make_groupmap(groups)
        context['registrations'] = self.make_registration_table(groupmap)
        context['total_line'] = self.make_total_line(groupmap)
        context['assistent_sum'] = self.make_assistent_sum()
        return context

    def make_groupmap(self, groups):
        groupmap = {}
        for (i,g) in enumerate(groups):
            groupmap[g.number] = i
        return groupmap

    def make_registration_table(self, groupmap):
        regtab = []
        groupcnt = len(groupmap)
        for group in groupmap.keys():
            regist_cnt = models.Registration.objects \
                .filter(group__number=group) \
                .values('student__group__number') \
                .order_by('student__group__number') \
                .annotate(count=Count('id'))
            row = (groupcnt+1) * [0]
            for d in regist_cnt:
                if d['student__group__number']==None:
                    i = groupcnt
                else:
                    i = groupmap[d['student__group__number']]
                row[i] = d['count']
            regtab.append([group] + row + [sum(row)])
        return regtab

    def make_total_line(self, groupmap):
        groupcnt = len(groupmap)
        total_cnt = models.Student.objects.get_pure_query_set() \
            .values('group__number').order_by('group__number') \
            .annotate(count=Count('id'))
        row = (groupcnt+1) * [0]
        for d in total_cnt:
            if d['group__number']==None:
                i = groupcnt
            else:
                i = groupmap[d['group__number']]
            row[i] = d['count']
        return ['total'] + row + [sum(row)]

    def make_assistent_sum(self):
        aq = models.Student.objects.get_pure_query_set() \
            .values('group__assistent').order_by('group__assistent') \
            .annotate(count=Count('id'))
        assist_info = {}
        for e in aq:
            ass_name = e['group__assistent']
            if ass_name:
                assist_info[ass_name] = [None, e['count']]

        group_list = models.Group.objects.all()
        assist_grp = {}
        for e in group_list:
            ai = assist_info[e.assistent]
            first_grp = ai[0]
            if not first_grp:
                ai[0] = e.number
                assist_grp[e.number] = [e.assistent, [e.number], ai[1]]
            else:
                assist_grp[first_grp][1].append(e.number)

        assist_list = []
        first_groups = assist_grp.keys()
        first_groups.sort()
        for grp in first_groups:
            assist_list.append(assist_grp[grp])
        return assist_list

query_regist = staff_member_required(QueryRegistrationsView.as_view())


class QueryNewAssignedView(TemplateView):
    template_name = 'student_manager/query_new_assigned.html'

    def get_context_data(self, **kwargs):
        context = super(QueryNewAssignedView, self) \
            .get_context_data(**kwargs)

        changed_assigned = models.Registration.objects.filter(status='ZU') \
            .exclude(group=F('student__group')) \
            .values('student__matrikel', 'student__last_name',
                    'student__first_name', 
                    'student__group__number', 'group__number') \
            .order_by('student__matrikel')
        context['changed_assigned'] = changed_assigned
        context['changed_count'] = changed_assigned.count()

        # new_assigned = models.Registration.objects \
        #     .filter(group=F('student__group')) \
        #     .exclude(status='ZU') \
        #     .exclude(student__matrikel=None) \
        #     .values('student__matrikel', 'student__last_name',
        #             'student__first_name', 'group') \
        #     .order_by('student__matrikel')
        # context['new_assigned'] = new_assigned
        # context['new_count'] = new_assigned.count()

        assigned_regist = models.Registration.objects.filter(status='ZU') \
            .values('student')
        not_assigned = models.Student.objects \
            .exclude(matrikel=None) \
            .exclude(group=None) \
            .exclude(id__in=assigned_regist) \
            .order_by('matrikel')
        context['not_assigned'] = not_assigned
        context['not_assigned_count'] = not_assigned.count()

        return context

query_new_assigned = staff_member_required(QueryNewAssignedView.as_view())


class ExportStudentsView(FormView):
    template_name = 'student_manager/export_students.html'
    form_class = forms.ExportStudentsForm

    def form_valid(self, form):
        export_choice = form.cleaned_data['export_choice']
        group = form.cleaned_data['group']
        if export_choice=='group':
            filename = 'gruppe%d.csv' % group.number
        else:
            filename = 'studenten.csv'

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = \
            'attachment; filename="%s"' % filename

        if export_choice=='group':
            qset = models.Student.objects.filter(group=group)
        else:
            qset = models.Student.objects.all()
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Matrikel', 'Name', 'Vorname',
                         'Fach', 'Semester', 'Gruppe'])
        for student in qset:
            writer.writerow([student.matrikel,
                             student.last_name.encode('utf-8'),
                             student.first_name.encode('utf-8'),
                             student.subject.encode('utf-8'),
                             student.semester, 
                             student.group])
        return response

export_students = staff_member_required(ExportStudentsView.as_view())


print_exsheet_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/print_exsheet_opt.html',
    form_class=forms.PrintExsheetOptForm))


class PrintExsheetView(ListView):
    template_name = 'student_manager/exsheet.html'

    def get(self, request):
        self.form = forms.PrintExsheetOptForm(request.GET)
        if self.form.is_valid():
            return super(PrintExsheetView, self).get(request)
        else:
            return render_to_response(
                'student_manager/print_exsheet_opt.html',
                {'form': self.form},
                 context_instance=RequestContext(request))

    def get_queryset(self):
        group = self.form.cleaned_data['group']
        students = models.Student.objects.filter(group=group, active=True) \
            .order_by('last_name', 'first_name')
        return students

    def get_context_data(self, **kwargs):
        context = super(PrintExsheetView, self).get_context_data(**kwargs)
        context['group'] = self.form.cleaned_data['group'].number
        return context

print_exsheet = staff_member_required(PrintExsheetView.as_view())


@staff_member_required
@require_POST
def save_exercise_results(request, queryset=None):
    if queryset is not None:
        # initial form
        students = models.Student.objects.filter(group__in=queryset) \
            .filter(active=True)
        formset = forms.ExerciseFormSet(queryset=students)
        sheet_form = forms.SheetForm()
    else:
        # submitted form
        sheet_form = forms.SheetForm(request.POST)
        formset = forms.ExerciseFormSet(request.POST)
        if sheet_form.is_valid():
            for form in formset:
                form.sheet = sheet_form.cleaned_data['sheet']
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Exercises updated.')
                return HttpResponseRedirect(
                    reverse('admin:student_manager_group_changelist'))

    return render_to_response(
        'student_manager/enter_exercise_results.html',
        {'formset': formset,
         'sheet_form': sheet_form,
         'groups': ', '.join([str(group) for group in queryset])},
        context_instance=RequestContext(request))


class QueryExerciseView(TemplateView):
    template_name = 'student_manager/query_exercise.html'

    def get_context_data(self, **kwargs):
        self.context = super(QueryExerciseView, self).get_context_data(**kwargs)

        groups = models.Group.objects.order_by('number')
        self.count_by_group(groups)
        return self.context

    def count_by_group(self, groups):
        tab = []
        max_sheet = 0
        for group in groups:
            ex_cnt = models.Exercise.objects \
                .filter(group=group) \
                .values('sheet') \
                .order_by('sheet') \
                .annotate(count=Count('id'))
            ex_cnt = list(ex_cnt)
            if not ex_cnt:
                continue
            sheets = ex_cnt[-1]['sheet']
            if sheets>=max_sheet:
                max_sheet = sheets
            row = sheets * [0]
            for d in ex_cnt:
                s = d['sheet']
                row[s-1] = d['count']
            tab.append([group] + row)
        self.context['data_by_group'] = tab
        head = [i for i in range(1,max_sheet+1)]
        self.context['head_by_group'] = ['Group'] + head
        self.count_total(max_sheet)

    def count_total(self, max_sheet):
        total_cnt = models.Exercise.objects \
            .values('sheet').order_by('sheet') \
            .annotate(count=Count('id'))
        row = max_sheet * [0]
        for d in total_cnt:
            s = d['sheet']
            row[s-1] = d['count']
        self.context['total'] = row

query_exercise = staff_member_required(QueryExerciseView.as_view())


