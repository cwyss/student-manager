"""Views"""

import csv, re, json
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Max, Count
from django.http import HttpResponseRedirect
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
        if self.stats['no_matrikel']:
            messages.warning(
                self.request,
                '%s entries without matrikel skipped.' \
                    % len(self.stats['no_matrikel']))
        
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


print_students_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/print_students_opt.html',
    form_class=forms.PrintStudentsOptForm))


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
                reverse('admin:student_manager_exam_changelist'))
        num_exercises_form = forms.NumberExercisesForm(request.POST)
        if num_exercises_form.is_valid():
            num_exercises = num_exercises_form.cleaned_data['num_exercises']
        else:
            raise ValidationError('Can\'t determine number of exercises')

    return render_to_response(
        'student_manager/enter_exam_results.html',
        {'formset': formset,
         'num_exercises': range(1, num_exercises + 1),
         'num_exercises_form': num_exercises_form},
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


class ImportRegistrationsView(FormView):
    template_name = 'student_manager/import_registration.html'
    form_class = forms.ImportRegistrationsForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']
        column_sep = str(form.cleaned_data['column_separator'])
        import_choice = str(form.cleaned_data['import_choice'])
        update_choice = str(form.cleaned_data['update_choice'])
        try:
            jstr = models.StaticData.objects. \
                get(key='subject_translation').value
            jstr = jstr.translate({0xa0: 32})
            self.subject_translation = json.loads(jstr)
        except models.StaticData.DoesNotExist:
            self.subject_translation = {}
        try:
            jstr = models.StaticData.objects. \
                get(key='group_translation').value
            jstr = jstr.translate({0xa0: 32})
            self.group_translation = json.loads(jstr)
        except models.StaticData.DoesNotExist:
            self.group_translation = {}
        self.stats = {'new': [],
                      'update': [],
                      'nogroup': []
                      }

        self.read_csv(csv_file, column_sep)
        # if update_choice in ('regist', 'all'):
        #     self.clear_existing_registrations()
        self.import_data(import_choice, update_choice)

        # messages.info(
        #     self.request,
        #     '%s entries processed.' % sum(map(len, self.stats.itervalues())))
        if import_choice!='none':
            msg = '%s new students created.'
            if import_choice=='stud':
                msg = 'Import student data: ' + msg
            else:
                msg = 'Import student and registration data: ' + msg
            messages.success(
                self.request,
                msg % len(self.stats['new']))
        if update_choice!='none':
            msg = 'data for %s existing students updated.'
            if update_choice=='stud':
                msg = 'Update student data: ' + msg
            elif update_choice=='regist':
                msg = 'Update registration data: ' + msg
            else:
                msg = 'Update student and registration data: ' + msg
            messages.success(
                self.request,
                msg % len(self.stats['update']))
        if self.stats['nogroup']:
            messages.warning(
                self.request,
                'no such group in translation: %s' \
                    % ', '.join(self.stats['nogroup'][:10]))

        return super(ImportRegistrationsView, self).form_valid(form)

    def read_csv(self, csv_file, column_sep):
        self.student_dict = {}
        csvreader = csv.reader(csv_file, delimiter=column_sep)
        header = True
        for line, row in enumerate(csvreader):
            if header:
                if len(row)==0 or not row[0].isdigit():
                    # We seem to have a header; ignore.
                    continue
                else:
                    header = False
            matrikel = int(row[0])
            if self.student_dict.has_key(matrikel):
                stud = self.student_dict[matrikel]
            else:
                long_subject = row[4].decode('UTF-8').translate({0xa0: 32})
                try:
                    subject = self.subject_translation[long_subject]
                except KeyError:
                    subject = long_subject
                stud = [row[1].decode('UTF-8'),  # last name
                        row[2].decode('UTF-8'),  # first name
                        subject,
                        int(row[6]),             # semester
                        []                       # registrations
                        ]
                self.student_dict[matrikel] = stud
            long_group = row[9].decode('UTF-8').translate({0xa0: 32})
            try:
                group = self.group_translation[long_group]
            except KeyError:
                self.stats['nogroup'].append(long_group)
                continue
            stud[4].append((group, 
                            row[7].decode('UTF-8'),  # status
                            int(row[8])              # priority
                            ))

    # def clear_existing_registrations(self):
    #     for matrikel in self.student_dict:
    #         try:
    #             student = models.Student.objects.get(matrikel=matrikel)
    #         except models.Student.DoesNotExist:
    #             continue
    #         models.Registration.objects.filter(student=student).delete()

    def import_data(self, import_choice, update_choice):
        for matrikel, stud in self.student_dict.iteritems():
            try:
                student = models.Student.objects.get(matrikel=matrikel)
                if update_choice=='none':
                    continue
                state = 'update'
                if update_choice in ('stud', 'all'):
                    student.last_name = stud[0]
                    student.first_name = stud[1]
                    student.subject = stud[2]
                    student.semester = stud[3]
                    student.save()
            except models.Student.DoesNotExist:
                if import_choice=='none':
                    continue
                student = models.Student(matrikel=matrikel,
                                         last_name=stud[0],
                                         first_name=stud[1],
                                         subject=stud[2],
                                         semester=stud[3])
                student.save()
                state = 'new'

            if update_choice in ('regist', 'all'):
                if state=='update':
                    models.Registration.objects.filter(student=student).delete()
                for regist in stud[4]:
                    registration = models.Registration(student=student,
                                                       group=regist[0],
                                                       status=regist[1],
                                                       priority=regist[2])
                    registration.save()
            self.stats[state].append(matrikel)


import_registrations = staff_member_required(ImportRegistrationsView.as_view())
