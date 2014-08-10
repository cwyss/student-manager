"""The admin page."""

from django.contrib import admin
from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from student_manager import forms, models, views


class GroupAdmin(admin.ModelAdmin):
    list_display = ('number', 'time', 'assistent')
    actions = ('enter_exercise_results',)
    form = forms.GroupForm

    def enter_exercise_results(self, request, queryset):
        return views.save_exercise_results(request, queryset)



class NonuniqueModuloMatrikelListFilter(admin.SimpleListFilter):
    title = _('modulo matrikel')
    parameter_name = 'modulo_matrikel'

    def lookups(self, request, model_admin):
        return (('nonunique', _('With non-unique modulo matrikel')),)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        if self.value() == 'nonunique':
            duplicates = models.Student.objects.get_pure_query_set()
            duplicates = duplicates.values('modulo_matrikel') \
                .annotate(Count('id'))
            duplicates = duplicates.values('modulo_matrikel').order_by()
            duplicates = duplicates.filter(id__count__gt=1)
            return queryset.filter(modulo_matrikel__in=duplicates)


class StudentAdmin(admin.ModelAdmin):
    list_display = ('matrikel', 'modulo_matrikel', 'obscured_matrikel',
                    'last_name', 'first_name', 'subject', 'semester',
                    'group', 'active', 'number_of_exercises', 'total_points',
                    'bonus')
    list_filter = (NonuniqueModuloMatrikelListFilter, 'active', 'group')
    search_fields = ('matrikel', 'last_name', 'first_name')
    form = forms.StudentForm
    actions = ('translate_subjects', 'toggle_active')

    def translate_subjects(self, request, queryset):
        subject_transl = models.StaticData.get_subject_transl()
        for (longname, shortname) in subject_transl.items():
            updateset = queryset.filter(subject=longname).values('id')
            # .values('id') noetig; 
            # vermutlich wegen annotation "total_points" aus
            # StudentManager model;
            # siehe: https://code.djangoproject.com/ticket/18580
            updateset.update(subject=shortname)

    def toggle_active(self, request, queryset):
        make_active = list(queryset.filter(active=False) \
            .values_list('id', flat=True))
        update_inactive = queryset.filter(active=True).values('id')
        update_inactive.update(active=False)
        update_active = queryset.filter(id__in=make_active).values('id')
        update_active.update(active=True)


class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('sheet', 'points', 'group', 'student')
    list_filter = ('sheet', 'group')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')


class MasterExamAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'mark_limits', 'num_exercises',
                    'max_points', 'part_points')
    form = forms.MasterExamForm


class RoomAdmin(admin.ModelAdmin):
    list_display = ('examnr', 'name', 'capacity', 'priority')
    list_filter = ('examnr',)


class ExamAdmin(admin.ModelAdmin):
    list_display = ('examnr', 'student', 'subject', 'number',
                    'room', 'resit', 'exam_group', 'points', 
                    'mark', 'final_mark')
    list_filter = ('examnr', 'subject', 'room', 'resit')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')
    actions = ('assign_seats', 'enter_results', 'enter_results_name_range')
    form = forms.ExamForm

    def assign_seats(self, request, queryset):
        examnr = queryset[0].examnr
        if queryset.exclude(examnr=examnr).exists():
            messages.error(request,
                           'Selection contains different exam numbers.')
            return
        rooms = models.Room.objects.filter(examnr=examnr).order_by('priority')
        roomlist = []
        maxnumber = 0
        for room in rooms:
            if room.capacity is None:
                 messages.error(request, 'Room %s has no capacity' % room)
                 return
            maxnumber += room.capacity
            roomlist.append((maxnumber, room))

        if maxnumber <= 0:
            messages.error(request,
                           'No rooms with capacity found for exam %s' % examnr)
            return

        queryset.update(number=None)
        queryset = queryset.order_by('student__modulo_matrikel',
                                     'student__obscured_matrikel')
        roomdata = roomlist.pop(0)
        for i, exam in enumerate(queryset):
            if i >= roomdata[0] and roomlist:
                roomdata = roomlist.pop(0)
            exam.number = i+1
            exam.room = roomdata[1]
            exam.save()
        messages.success(request, 'Assigned %s seats' % queryset.count())


    def enter_results(self, request, queryset):
        return views.save_exam_results(request, queryset)


    def enter_results_name_range(self, request, queryset):
        exam_selection = list(queryset)
        name_start = exam_selection[0].student.last_name
        name_end = exam_selection[-1].student.last_name
        examnr = exam_selection[0].examnr
        queryset = models.Exam.objects.filter(examnr=examnr) \
            .filter(student__last_name__gte=name_start) \
            .filter(student__last_name__lte=name_end)
        if not queryset:
            messages.warning(
                request,
                'Resulting exam range is empty.')
            return HttpResponseRedirect(
                reverse('admin:student_manager_exam_changelist'))
        else:
            return views.save_exam_results(request, queryset)


class ExamPartAdmin(admin.ModelAdmin):
    list_display = ('exam', 'number', 'points')
    list_filter = ('number',)
    raw_id_fields = ('exam',)
    search_fields = ('exam__student__matrikel', 'exam__student__last_name',
                     'exam__student__first_name')

    def save_model(self, request, obj, form, change):
        super(ExamPartAdmin, self).save_model(request, obj, form, change)
        exam = obj.exam
        total_points = exam.exampart_set.aggregate(Sum('points'))['points__sum']
        exam.points = total_points
        exam.save()


class StaticDataAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    form = forms.StaticDataForm


class AssignedGroupListFilter(admin.SimpleListFilter):
    title = 'assigned group'
    parameter_name = 'assigned_group'

    def lookups(self, request, model_admin):
        groupset = models.Registration.objects \
            .values('student__group__number') \
            .order_by('student__group__number') \
            .annotate(Count('id'))
        lookups = []
        for x in groupset:
            group = x['student__group__number']
            if group!=None:
                lookups.append((group, str(group)))
            else:
                lookups.append((False, 'None'))
        return lookups

    def queryset(self, request, queryset):
        if self.value()==None:
            return queryset
        elif self.value()=='False':
            return queryset.filter(student__group__isnull=True)
        else:
            return queryset.filter(student__group__number=self.value())

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'priority', 'status',
                    'assigned_group')
    list_filter = ('group', AssignedGroupListFilter, 'priority', 'status')
    raw_id_fields = ('student',)
    search_fields = ('student__matrikel', 'student__last_name',
                     'student__first_name')
    actions = ('assign_groups',)

    def assign_groups(self, request, queryset):
        duplicates = queryset.values('student') \
            .order_by('student') \
            .annotate(count=Count('id')).filter(count__gte=2)
        if duplicates:
            out = []
            for e in duplicates:
                student = models.Student.objects.get(id=e['student'])
                out.append(str(student))
            messages.error(
                request,
                'Selection contains multiple registrations for ' + \
                    ', '.join(out))
            return
        for regist in queryset:
            student = regist.student
            student.group = regist.group
            student.save()
        messages.success(
            request,
            'Assigned groups to %d students' % queryset.count())



admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.Student, StudentAdmin)
admin.site.register(models.Exercise, ExerciseAdmin)
admin.site.register(models.MasterExam, MasterExamAdmin)
admin.site.register(models.Room, RoomAdmin)
admin.site.register(models.Exam, ExamAdmin)
admin.site.register(models.ExamPart, ExamPartAdmin)
admin.site.register(models.StaticData, StaticDataAdmin)
admin.site.register(models.Registration, RegistrationAdmin)
