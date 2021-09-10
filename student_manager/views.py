"""Views"""

import csv, re, json, urllib
import xml.etree.ElementTree as ElementTree
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Max, Count, F, Sum
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
        importformat = form.cleaned_data['format']
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
            if importformat == 'exerc':
                self.save_exercise(group, student, row[1], row[2])
            else:
                if form.cleaned_data['format'] == 'sheet':
                    pointenum = enumerate(row[1:])
                else:
                    group = models.Group.objects.get(number=row[1])
                    pointenum = enumerate(row[2:])
                for i, points in pointenum:
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
        if points.strip() in ('','-'):
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
            students = students.order_by('modulo_matrikel',
                                         'obscured_matrikel')
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
        selection = self.request.GET.get('selection')
        group = self.request.GET.get('group')
        exclude = self.request.GET.get('exclude')
        total = self.request.GET.get('total')
        etest = self.request.GET.get('etest')
        maxsheet = self.request.GET.get('maxsheet')

        if not maxsheet:
            maxsheet = models.Exercise.total_num_exercises()
        else:
            maxsheet = int(maxsheet)
            
        try:
            maxpoints = float(models.StaticData.objects.get(
                    key='maxpoints').value)
        except models.StaticData.DoesNotExist:
            maxpoints = None
        try:
            models.StaticData.objects.get(key='require_etest')
            etest_required = True
        except models.StaticData.DoesNotExist:
            etest_required = False

        # exclude students coming only from exam entries
        students = models.Student.objects.exclude(group=None)

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
            student.exercises = [None] * maxsheet
            for exercise in student.exercise_set.all():
                if exercise.sheet<=maxsheet:
                    student.exercises[exercise.sheet-1] = exercise
            if etest_required and \
               ( not student.entrytest_set.exists() \
                 or student.entrytest_set.get().result=='fail'):
                student.etest_fail = True
            if maxpoints:
                student.percent = float(student.total_points()) \
                                  / maxpoints * 100
            else:
                student.percent = None
            student_data.append(student)

        return student_data

    def get_context_data(self, **kwargs):
        context = super(PrintExercisesView, self).get_context_data(**kwargs)
        context['lecture'] = models.StaticData.get_lecture_name()
        selection = self.request.GET.get('selection')
        if selection=='matrikel':
            context['matrikel'] = True
        else:
            context['matrikel'] = False
        if models.StaticData.get_points_div()==4:
            context['points_doubledigits'] = True
        else:
            context['points_doubledigits'] = False
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
        csvreader = csv.reader(
            form.cleaned_data['csv_file'],
            delimiter=str(form.cleaned_data['column_separator']))
        self.examnr = form.cleaned_data['examnr']
        self.stats = {'newstud': [],
                      'new': [],
                      'updated': [],
                      'unchanged': [],
                      'error': []
                      }
        self.subjectcnt = 0
        self.subject = None
        for linenr, row in enumerate(csvreader):
            if len(row)==0:
                pass
            elif row[0].startswith('subject:'):
                self.subject = row[0][8:].strip()
                self.subjectcnt += 1
            else:
                self.examine_row(linenr, row)

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
            for linenr in self.stats['error'][:10]:
                messages.warning(
                    self.request,
                    'Format error line %d' % (linenr+1))
        return super(ImportExamsView, self).form_valid(form)

    def examine_row(self, linenr, row):
        try:
            name = row[1].decode('UTF-8')
            first_name = row[2].decode('UTF-8')
            matr = int(row[3])
            if len(row)>=5 and len(row[-1])>0:
                resit = int(row[-1])
            else:
                resit = None
        except (IndexError, ValueError):
            self.stats['error'].append(linenr)
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
        self.stats[status].append(linenr)


#     def examine_line(self, line):
#         if line.startswith('subject:'):
#             self.subject = line[8:].strip()
#             self.subjectcnt += 1
#             return None
#         elif line.isspace():
#             return None
#         cols = self.find_columns(line)
#         if cols:
#             return cols
#         else:
#             self.stats['error'].append(line)
#             return None

#     def find_columns(self, line):
#         m = re.match(r"\s*(\d+) (.+?) (\d+)\s+(\d)", line, re.U)
#         if not m:
#             return None
#         m2 = re.match(r"\s*(\S.+?)  \s*(\S.+)", m.group(2), re.U)
#         if not m2:
#             m2 = re.match(r"\s*(\S+?) (\S+?)\s*\Z", m.group(2), re.U)
#         if not m2:
#             return None
#         return (m.start(2), m.start(2)+m2.start(2), m.end(3)-7, m.start(4))

#     def save_exam(self, line, cols):
# #        nr = int(line[:cols[0]])
#         try:
#             name = line[cols[0]:cols[1]].strip()
#             first_name = line[cols[1]:cols[2]].strip()
#             matr = int(line[cols[2]:cols[3]])
#             resit = int(line[cols[3]:].split()[-1])
#         except (IndexError, ValueError):
#             self.stats['error'].append(line)
#             return
#         try:
#             student = models.Student.objects.get(matrikel=matr)
#         except models.Student.DoesNotExist:
#             student = models.Student(matrikel=matr,
#                                      last_name=name,
#                                      first_name=first_name,
#                                      subject=self.subject)
#             student.save()
#             status = 'newstud'
#         else:
#             status = 'new'
#         try:
#             exam = models.Exam.objects.get(student=student, examnr=self.examnr)
#             if exam.subject==self.subject and exam.resit==resit:
#                 status = 'unchanged'
#             else:
#                 status = 'updated'
#         except models.Exam.DoesNotExist:
#             exam = models.Exam(student=student,
#                                examnr=self.examnr)
#         exam.subject = self.subject
#         exam.resit = resit
#         exam.save()
#         self.stats[status].append(line)

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

        if format.startswith('exam'):
            self.map_seats(exams, examnr)
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

    def map_seats(self, exams, examnr):
        seat_map = {}
        room_out_of_seats = []
        for room in models.Room.objects.filter(examnr=examnr):
            if room.first_seat and room.seat_map:
                seat_map[room] = (room.first_seat, json.loads(room.seat_map))
        for e in exams:
            if seat_map.has_key(e.room):
                (first,seats) = seat_map[e.room]
                try:
                    e.seat = seats[e.number-first]
                except IndexError:
                    if not e.room in room_out_of_seats:
                        room_out_of_seats.append(e.room)
            else:
                e.seat = e.number
        if room_out_of_seats:
            messages.error(self.request,
                             'Not enough entries in seat map for room(s) ' + \
                             ','.join([r.name for r in room_out_of_seats]))
            self.template_name='student_manager/print_exams_opt.html'
            
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


class PointGroup(object):
    def __init__(self, previous=None, step=2):
        if not previous:
            self.step = step
            self.lower = 0
            self.upper = step
        else:
            self.step = previous.step
            self.lower = previous.upper
            self.upper = self.lower + self.step
        self.count = 0

def collect_pointgroups(queryset, pointstep=2, max_points=None):
        group = PointGroup(step=pointstep)
        pointgroups = [group]
        for item in queryset:
            while item['points'] >= group.upper:
                group = PointGroup(previous=group)
                pointgroups.append(group)
            group.count += item['count']
        if max_points and group.upper > max_points:
            del pointgroups[-1]
            pointgroups[-1].count += group.count
        return pointgroups


query_exams_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/query_exams_opt.html',
    form_class=forms.QueryExamsOptForm))


class QueryExamsView(TemplateView):
    template_name = 'student_manager/query_exams.html'

    def get_context_data(self, **kwargs):
        context = super(QueryExamsView, self).get_context_data(**kwargs)
        examnr = self.request.GET.get('examnr')
        query_examgroups = self.request.GET.get('query_examgroups')

        exams = models.Exam.objects.filter(examnr=examnr)
        examlist = exams.exclude(points=None)
        context['total_count'] = self.count_apf(examlist)
        context['missing_count'] = exams.filter(points=None).count()

        if query_examgroups:
            self.get_examgroups(examlist)
            context['groups_count'] = []
            for group in self.exam_groups:
                group_query = examlist.filter(exam_group=group)
                group_count = self.count_apf(group_query)
                group_count['group'] = group
                context['groups_count'].append(group_count)

        if not query_examgroups:
            markcounts = examlist.values('mark').order_by('mark') \
                .annotate(total=Count('id'))
            context['markcounts'] = markcounts
        else:
            context['markcounts'] = self.count_mark_groups(examlist)

        pointcounts = examlist.values('points').order_by('points') \
            .annotate(count=Count('id'))
        masterexam = models.MasterExam.objects.get(id=examnr)
        try:
            pointstep = int(models.StaticData.objects.get(
                    key='query_exam_pointstep').value)
        except models.StaticData.DoesNotExist:
            pointstep = 2
        context['pointgroups'] = collect_pointgroups(
            pointcounts,
            pointstep,
            max_points = masterexam.max_points)
        return context

    def count_apf(self, queryset):
        return {'attend': queryset.count(),
                'pass': queryset.filter(mark__lte=4.0).count(),
                'fail': queryset.filter(mark=5.0).count()
                }

    def get_examgroups(self, examlist):
        query = examlist.values('exam_group').order_by('exam_group') \
            .annotate(count=Count('id'))
        self.exam_groups = []
        for item in query:
            self.exam_groups.append(item['exam_group'])

    def count_mark_groups(self, examlist):
        query = examlist.values('mark', 'exam_group') \
            .order_by('mark', 'exam_group') \
            .annotate(count=Count('id'))
        numgroups = len(self.exam_groups)
        markcounts = [] 
        mark_entry = {'groupcounts': [0]*numgroups}
        for item in query:
            if mark_entry.has_key('mark') and \
                    mark_entry['mark']!=item['mark']:
                mark_entry['total'] =  sum(mark_entry['groupcounts'])
                markcounts.append(mark_entry)
                mark_entry = {'groupcounts': [0]*numgroups}
            mark_entry['mark'] = item['mark']
            group_index = self.exam_groups.index(item['exam_group'])
            mark_entry['groupcounts'][group_index] = item['count']
        if mark_entry.has_key('mark'):
            mark_entry['total'] = sum(mark_entry['groupcounts'])
            markcounts.append(mark_entry)
        return markcounts


query_exams = staff_member_required(QueryExamsView.as_view())


query_examparts_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/query_examparts_opt.html',
    form_class=forms.QueryExamPartsOptForm))


class QueryExamPartsView(TemplateView):
    template_name = 'student_manager/query_examparts.html'

    def get_context_data(self, **kwargs):
        context = super(QueryExamPartsView, self).get_context_data(**kwargs)
        examnr = self.request.GET.get('examnr')
        masterexam = models.MasterExam.objects.get(id=examnr)
        if masterexam.part_points:
            part_points = json.loads(masterexam.part_points)
        else:
            part_points = None

        parts = models.ExamPart.objects.filter(exam__examnr=examnr) \
            .exclude(points=None)
        counts = parts.values('number').order_by('number') \
            .annotate(count=Count('id'), sum=Sum('points'))
        for item in counts:
            item['average'] = item['sum']/item['count']
            if part_points:
                item['percent'] = \
                    100 * item['average'] / part_points[item['number']-1]
        context['counts'] = counts

        return context


query_examparts = staff_member_required(QueryExamPartsView.as_view())


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


class ImportEntryTestsView(FormView):
    template_name = 'student_manager/import_entrytest.html'
    form_class = forms.ImportEntryTestsForm

    def get_success_url(self):
        return self.request.GET.get('return_url', '/')

    def form_valid(self, form):
        csvreader = csv.reader(
            form.cleaned_data['csv_file'],
            delimiter=str(form.cleaned_data['csv_separator']))
        results = {'bestanden': 'pass',
                   'nicht bestanden': 'fail',
                   'pass': 'pass',
                   'fail': 'fail',
                   '-': None,
                   '': None
        }
        self.stats = {'new': [],
                      'update': [],
                      'unknown': [],
                      'error': []
        }

        for line, row in enumerate(csvreader):
            if line == 0 and not row[0].isdigit():
                # We seem to have a header; ignore.
                continue

            if row[0].isdigit():
                matrikel = int(row[0])
                res_field = row[1].decode('UTF-8').strip('"')
                try:
                    result = results[res_field]
                    if not result:
                        # line without test result
                        continue
                    try:
                        student = models.Student.objects.get(matrikel=matrikel)
                        status = self.save_etest(student, result)
                    except models.Student.DoesNotExist:
                        status = 'unknown'
                except KeyError:
                    status = 'error'
            else:
                status = 'error'

            if status=='error':
                self.stats['error'].append(line+1)
            elif status!=None:
                self.stats[status].append(matrikel)

        if self.stats['new']:
            messages.success(
                self.request,
                '%d new test(s) created' % len(self.stats['new']))
        if self.stats['update']:
            messages.success(
                self.request,
                '%d test(s) updated' % len(self.stats['update']))
        if self.stats['unknown']:
            lst = ['%d' % m for m in self.stats['unknown']]
            messages.warning(
                self.request,
                "unknown student(s): %s" % ', '.join(lst))
        if self.stats['error']:
            lst = ["%d" % m for m in self.stats['error']]
            messages.warning(
                self.request,
                "csv file: error in line(s) %s" % ', '.join(lst))
        return super(ImportEntryTestsView, self).form_valid(form)

    def save_etest(self, student, result):
        try:
            etest = models.EntryTest.objects.get(student=student)
            if etest.result!=result:
                etest.result = result
                status = 'update'
            else:
                # unchanged test result
                return None
        except models.EntryTest.DoesNotExist:
            etest = models.EntryTest(student=student,
                                     result=result)
            status = 'new'
        etest.save()
        return status

    
import_entrytests = staff_member_required(ImportEntryTestsView.as_view())


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

    class AssistList:
        class Assistent:
            def __init__(self, name, first_group):
                self.name = name
                self.first_group = first_group
                self.groups = [first_group]
                self.students = 0
                
            def add_students(self, count):
                self.students += count

        def __init__(self):
            self.name_dict = {}
            # self.group_dict = {}

        def add(self, name, group):
            if self.name_dict.has_key(name):
                a = self.name_dict[name]
                a.groups.append(group)
            else:
                a = self.Assistent(name, group)
                self.name_dict[name] = a
            # self.group_dict[group] = a

    def make_assistent_sum(self):
        assist_list = self.AssistList()
        group_list = models.Group.objects.all().order_by('number')
        for g in group_list:
            if g.assistent:
                assist_list.add(g.assistent, g.number)
        query = models.Student.objects.get_pure_query_set() \
            .values('group__assistent').order_by('group__assistent') \
            .annotate(count=Count('id'))
        for e in query:
            name = e['group__assistent']
            if name:
                a = assist_list.name_dict[name]
                a.add_students(e['count'])
        assist_sum = []
        for a in assist_list.name_dict.values():
            assist_sum.append([a.name, a.groups, a.students])
        assist_sum.sort(key=lambda e:e[1][0])
        return assist_sum

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

        response = HttpResponse(content_type='text/csv')
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
        groups_form = forms.GroupsForm()
        groups_form.fields['groups'].initial = [g.id for g in queryset]
    else:
        # submitted form
        sheet_form = forms.SheetForm(request.POST)
        groups_form = forms.GroupsForm(request.POST)
        formset = forms.ExerciseFormSet(request.POST)
        if sheet_form.is_valid():
            for form in formset:
                form.sheet = sheet_form.cleaned_data['sheet']
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Exercises updated.')
                return HttpResponseRedirect(
                    reverse('admin:student_manager_group_changelist'))
        assert groups_form.is_valid()
        queryset = groups_form.cleaned_data['groups']

    return render_to_response(
        'student_manager/enter_exercise_results.html',
        {'formset': formset,
         'sheet_form': sheet_form,
         'groups_form': groups_form,
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


query_special_opt = staff_member_required(FormView.as_view(
    template_name='student_manager/query_special_opt.html',
    form_class=forms.QuerySpecialOptForm))


class QuerySpecialView(TemplateView):
    template_name = 'student_manager/query_special.html'

    def get_context_data(self, **kwargs):
        context = super(QuerySpecialView, self).get_context_data(**kwargs)
        select_query = self.request.GET.get('select_query')

        queries = {'exam_exercise': self.mkque_exam_exercise,
                   'exam_subject': self.mkque_exam_subject,
                   'exam_first': self.mkque_exam_first_sem,
                   'exam_both': self.mkque_exam_both,
                   'exam_group': self.mkque_exam_group,
                   'exgroup_diff': self.mkque_exgroup_diff
               }
        q = queries[select_query]
        q()

        context['infotext'] = self.infotext
        context['headline'] = self.headline
        context['data'] = self.data
        return context

    def mkque_exam_both(self):
        self.infotext = "Results for both exams: figures are 'pass' / 'total'; " \
                        + "column 'jointly' counts each student only once"

        exams_all = models.Exam.objects.all()
        exams_fk6 = exams_all.filter(subject__in=('ET','IT','WIng','Kombi ET'))
        exams_sem12 = exams_all.filter(student__semester__lte=2)
        exams_fk6sem12 = exams_fk6.filter(student__semester__lte=2)

        self.headline = ['group','exam 1','%','exam 2','%','jointly','%']
        self.data = []

        for (group, query) in (('all',exams_all), ('fk6',exams_fk6), ('1st year all', exams_sem12),
                               ('1st year fk6', exams_fk6sem12)):
            line = [group]
            for i in (1,2):
                exams = query.filter(examnr__number=i)
                cnt_pass = exams.filter(mark__lte=4.0).count()
                cnt_tot = exams.filter(mark__lte=5.0).count()
                if cnt_tot>0:
                    rel_pass = Decimal('100.')*cnt_pass/cnt_tot
                    rel_pass = rel_pass.quantize(Decimal('99.0'))        # round to 1 decimal place
                else:
                    rel_pass = 0
                line.append("%d/%d" % (cnt_pass,cnt_tot))
                line.append(rel_pass)
            
            exams_pass = query.filter(mark__lte=4.0) \
                              .values('student__matrikel') \
                              .annotate(exam_count=Count('id'))
            cnt_pass = exams_pass.count()
            exams_tot = query.filter(mark__lte=5.0) \
                            .values('student__matrikel') \
                            .annotate(exam_count=Count('id'))
            cnt_tot = exams_tot.count()
            if cnt_tot>0:
                rel_pass = Decimal('100.')*cnt_pass/cnt_tot
                rel_pass = rel_pass.quantize(Decimal('99.0'))        # round to 1 decimal place
            else:
                rel_pass = 0
            line.append("%d/%d" % (cnt_pass,cnt_tot))
            line.append(rel_pass)

            self.data.append(line)
            
    def mkque_exam_first_sem(self):
        self.infotext = 'exam results for first semester students (for exam 1)'

        exams = models.Exam.objects \
                .filter(examnr__number=1, student__semester__lte=1, mark__lte=5.0)

        exams_fk6 = exams.filter(subject__in=('ET','IT','WIng','Kombi ET'))
        exams_et = exams.filter(subject='ET')
        exams_it = exams.filter(subject='IT')
        exams_wing = exams.filter(subject='WIng')
                
        self.headline = ['group','pass','total','%']
        self.data = []

        for (group, query) in (('ET',exams_et), ('IT',exams_it), ('WIng',exams_wing),
                               ('FK6',exams_fk6), ('all',exams)):
            cnt_pass = query.filter(mark__lte=4.0).count()
            cnt_tot = query.count()
            if cnt_tot>0:
                rel_pass = Decimal('100.')*cnt_pass/cnt_tot
                rel_pass = rel_pass.quantize(Decimal('99.0'))              # round to 1 decimal places
            else:
                rel_pass = 0
            self.data.append((group, cnt_pass, cnt_tot, rel_pass))
        
    def mkque_exam_subject(self):
        self.infotext = 'exam pass/fail count by subject (for exam 1)'

        exams = models.Exam.objects \
                .filter(examnr__number=1)
        
        exams_pass=exams.filter(mark__lte=4.0) \
                        .values('subject').order_by('subject') \
                        .annotate(count=Count('id'))
        exams_fail=exams.filter(mark=5.0) \
                        .values('subject').order_by('subject') \
                        .annotate(count=Count('id'))

        pfdict = {}
        for e in exams_pass:
            pfdict[e['subject']] = (e['count'],0)
        for e in exams_fail:
            pf = pfdict.get(e['subject'], (0,0))
            pfdict[e['subject']] = (pf[0],e['count'])

        self.data = []
        for (s,v) in pfdict.iteritems():
            tot = v[0]+v[1]
            rel = Decimal('100.')*v[0]/tot
            rel = rel.quantize(Decimal('99.0'))                   # round to 1 decimal place
            self.data.append((s,v[0],v[1],tot,rel))
        self.data.sort(key=lambda x: x[0])
        
        self.headline = ['subject','pass','fail','total','% pass']
    
    def mkque_exam_group(self):
        self.infotext = 'exam pass/fail count by group (for exam 1)'

        exams = models.Exam.objects \
                .filter(examnr__number=1)
        
        exams_pass=exams.filter(mark__lte=4.0) \
                        .values('student__group__number').order_by('student__group__number') \
                        .annotate(count=Count('id'))
        exams_fail=exams.filter(mark=5.0) \
                        .values('student__group__number').order_by('student__group__number') \
                        .annotate(count=Count('id'))
        exams_lowpass=exams.filter(mark__lte=4.0, mark__gt=3.0) \
                        .values('student__group__number').order_by('student__group__number') \
                        .annotate(count=Count('id'))

        pfdict = {}
        for e in exams_pass:
            pfdict[e['student__group__number']] = (e['count'],0,0)
        for e in exams_fail:
            pf = pfdict.get(e['student__group__number'], (0,0,0))
            pfdict[e['student__group__number']] = (pf[0],e['count'],0)
        for e in exams_lowpass:
            pf = pfdict.get(e['student__group__number'], (0,0,0))
            pfdict[e['student__group__number']] = (pf[0],pf[1],e['count'])

        self.data = []
        for (s,v) in pfdict.iteritems():
            tot = v[0]+v[1]
            rel = Decimal('100.')*v[0]/tot
            rel = rel.quantize(Decimal('99.0'))                   # round to 1 decimal place
            self.data.append((s,v[0],v[1],tot,rel,v[2]))
        # self.data.sort(key=lambda x: x[0])
        
        self.headline = ['group','pass','fail','total','% pass','bad pass (>3.0)']
    
    def mkque_exam_exercise(self):
        self.infotext = "exam points vs exercise points"
        exam = models.Exam.objects \
               .annotate(exercise_points=Sum('student__exercise__points')) \
               .filter(points__gte=25) \
               .values('student__matrikel',
                       'student__last_name', 'student__semester', 'points',
                       'exercise_points') \
               .order_by('points')

        exam = filter(lambda e: e['exercise_points']>=15, exam)
        self.data = []
        for e in exam:
            self.data.append((e['student__matrikel'],
                              e['student__last_name'],
                              e['student__semester'],
                              e['points'],
                              e['exercise_points']))
        self.headline = []
        self.infotext += " (entries: %d)" % len(self.data)

    def mkque_exgroup_diff(self):
        self.infotext = "Exercises of students from different group"

        groups = models.Group.objects.order_by('number')
        self.data = []
        for group in groups:
            line = [group]
            ex_cnt = models.Exercise.objects \
                                    .filter(group=group) \
                                    .exclude(student__group=group) \
                                    .values('sheet') \
                                    .order_by('sheet') \
                                    .annotate(count=Count('id'))
            for e in ex_cnt:
                line.append(e['count'])
            self.data.append(line)
        self.headline = []

                
query_special = staff_member_required(QuerySpecialView.as_view())
