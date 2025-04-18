"""Forms."""

from decimal import Decimal
import json
from django import forms
from django.forms.utils import ErrorList
from django.forms.models import (
    modelformset_factory,
    modelform_factory,
    BaseModelFormSet)
from django.forms.widgets import HiddenInput, TextInput, NumberInput
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from student_manager import models


class GroupForm(forms.ModelForm):
    class Meta:
        model = models.Group
        exclude = ()
        
    def clean_time(self):
        time = self.cleaned_data['time']
        return time.translate({0xa0: 32})


class StudentForm(forms.ModelForm):
    class Meta:
        model = models.Student
        exclude = ('modulo_matrikel',)
        widgets = {
            "matrikel": NumberInput(attrs={"size": 8})
        }

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        models.validate_matrikel(matrikel, student_id)
        return matrikel


class StaticDataForm(forms.ModelForm):
    class Meta:
        model = models.StaticData
        exclude = ()

    def clean_value(self):
        key = self.cleaned_data['key']
        value = self.cleaned_data['value']
        if key=='subject_translation':
            try:
                transl = json.loads(value)
                if type(transl)!=dict:
                    raise ValueError
            except ValueError:
                raise ValidationError('Invalid translation.')
        return value


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = models.Exercise
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ExerciseForm, self).__init__(*args, **kwargs)
        self.fields['points'] = forms.TypedChoiceField(
            required=False,
            choices=models.points_choices(),
            coerce=Decimal)


class MasterExamForm(forms.ModelForm):
    class Meta:
        model = models.MasterExam
        exclude = ()

    def clean_mark_limits(self):
        mark_limits_str = self.cleaned_data['mark_limits']
        if mark_limits_str:
            try:
                mark_limits = json.loads(mark_limits_str)
                if type(mark_limits) != list:
                    raise ValueError
                for entry in mark_limits:
                    if type(entry) != list or len(entry) != 2:
                        raise ValueError
            except ValueError:
                raise ValidationError('Expect list of point-mark-tuples')
        return mark_limits_str


class ExamForm(forms.ModelForm):
    class Meta:
        model = models.Exam
        fields = ('examnr', 'student', 'subject', 'number',
                  'room', 'resit', 'exam_group', 'points')


class ExamResultForm(forms.ModelForm):
    class Meta:
        model = models.Exam
        fields = ('exam_group',)

    def __init__(self, *args, **kwargs):
        super(ExamResultForm, self).__init__(*args, **kwargs)
        exam = kwargs['instance']
        self.fields['exam_group'].widget = TextInput(attrs={'class':'exam_group'})
        self.num_exercises = exam.examnr.num_exercises
        for i in range(self.num_exercises):
            try:
                initial = exam.exampart_set.filter(number=i+1)[0].points
            except IndexError:
                initial = None
            self.fields['subpoints_%i' % i] = forms.DecimalField(
                required=False,
                initial=initial,
                widget=TextInput(attrs={'class':'subpoints',
                                        'onchange': 'updateTotal(this);'}))

        self.fields['points'] = forms.DecimalField(
            required=False,
            initial=exam.points,
            widget=TextInput(attrs={'class':'total'}))

    def save(self, commit=True):
        instance = super(ExamResultForm, self).save(commit)
        instance.points = self.cleaned_data['points']
        if commit:
            instance.save()
            for i in range(self.num_exercises):
                exampart, created = instance.exampart_set.get_or_create(
                    number=i+1)
                exampart.points = self.cleaned_data['subpoints_%i' % i]
                exampart.save()
        return instance


ExamFormSet = modelformset_factory(
    models.Exam,
    form=ExamResultForm,
    extra=0)


class NumberExercisesForm(forms.Form):
    num_exercises = forms.IntegerField(widget=HiddenInput)


class ImportExercisesForm(forms.Form):
    group = forms.ModelChoiceField(required=False,
        queryset=models.Group.objects.all())
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))
    format = forms.ChoiceField(choices=(
        ('', 'Please select'),
        ('exerc', 'Exercise table (one entry per exercise)'),
        ('sheet', 'Big table (one column per sheet)'),
        ('sheet-wgrp', 'Big table with group entry')))

    def clean(self):
        if self.cleaned_data.get('format')!='sheet-wgrp' and \
           self.cleaned_data.get('group')==None:
            raise ValidationError('No group selected.')
        return self.cleaned_data


class ImportStudentsForm(forms.Form):
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))


class PrintGroupsOptForm(forms.Form):
    matrikel = forms.ChoiceField(label=_('Selection'),
                                 choices=(('on', 'Students with matrikel'),
                                          ('', 'Students without matrikel')),
                                 initial='on')


class PrintExercisesOptForm(forms.Form):
    selection = forms.ChoiceField(
        label=_('Selection'),
        choices=(('matrikel', 'Students with matrikel'),
                 ('nomatrikel', 'Students without matrikel'),
                 ('group', 'Students from group...')),
        initial='matrikel')
    group = forms.ModelChoiceField(
        queryset=models.Group.objects.all(),
        required=False)
    total = forms.BooleanField(label=_('Display total/bonus columns'),
                               required=False)
    etest = forms.BooleanField(label=_('Display entry test column'),
                               required=False)
    exclude = forms.ChoiceField(
        choices=(('empty', 'Exclude students without exercises'),
                 ('inactive', 'Exclude inactive students')),
        initial='inactive')
    maxsheet = forms.IntegerField(label='Sheets up to (optional)',
                                  required=False)
    

class PrintStudentsOptForm(forms.Form):
    order_by = forms.ChoiceField(choices=(('matrikel', 'matrikel number'),
                                          ('name', 'name')))


class ImportExamsForm(forms.Form):
    examnr = forms.ModelChoiceField(
        label='Exam number',
        queryset=models.MasterExam.objects.all())
    csv_file = forms.FileField(label=_('CSV File'))
    column_separator = forms.CharField(max_length=1, initial=';')


class PrintExamsOptForm(forms.Form):
    examnr = forms.ModelChoiceField(
        label='Exam number',
        queryset=models.MasterExam.objects.all())
    format = forms.ChoiceField(
        choices=(('exam_obscured', 'seat list - with obscured matrikel'),
                 ('exam_full', 'seat list - with full data'),
                 ('result_obscured', 'result list - with obscured matrikel'),
                 ('result_full', 'result list - with full data')))


class QueryExamsOptForm(forms.Form):
    examnr = forms.ModelChoiceField(
        label='Exam number',
        queryset=models.MasterExam.objects.all())
    query_examgroups = forms.BooleanField(
        label='Distinguish exam groups',
        required=False
    )


class QueryExamPartsOptForm(forms.Form):
    examnr = forms.ModelChoiceField(
        label='Exam number',
        queryset=models.MasterExam.objects.all())


class QueryStudentsOptForm(forms.Form):
    first_field = forms.ChoiceField(
        choices=(('subject', 'Subject'),
                 ('semester', 'Semester'),
                 ('group', 'Group'),
                 ('active', 'Active')))
    second_field = forms.ChoiceField(
        choices=(('none', 'None'),
                 ('subject', 'Subject'),
                 ('semester', 'Semester'),
                 ('group', 'Group'),
                 ('active', 'Active')))
    only_active = forms.BooleanField(
        label=_('Include only active students'),
        initial=True,
        required=False
    )


class ImportRegistrationsForm(forms.Form):
    file = forms.FileField(label=_('CSV or Wusel XLS file'))
    csv_separator = forms.CharField(max_length=1, initial=';')
    update_choice = forms.ChoiceField(
        label='Update data for existing students?',
        choices=(('none', "don't update existing data"),
                 ('stud', 'update only student data'),
                 ('regist', 'update only registration data'),
                 ('all', 'update student and registration data'))
        )
    import_choice = forms.ChoiceField(
        label='Import data for new students?',
        choices=(('none', "don't import new data"),
                 ('stud', 'import only student data'),
                 ('all', 'import student and registration data'))
        )
    create_groups = forms.BooleanField(
        label='Create non-existing groups?',
        required=False)


class ImportEntryTestsForm(forms.Form):
    csv_file = forms.FileField(label=_('CSV file'))
    csv_separator = forms.CharField(max_length=1, initial=';')


class ExportStudentsForm(forms.Form):
    export_choice = forms.ChoiceField(
        choices=(('group', 'Students from group...'),
                 ('all', 'All students')))
    group = forms.ModelChoiceField(required=False,
        queryset=models.Group.objects.all())

    def clean(self):
        group = self.cleaned_data.get('group')
        if self.cleaned_data.get('export_choice')=='group' and \
                not models.Student.objects.filter(group=group).exists():
            raise ValidationError('No students in this group.')
        return self.cleaned_data


class PrintExsheetOptForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=models.Group.objects.all())

    def clean_group(self):
        group = self.cleaned_data['group']
        if not models.Student.objects.filter(group=group, active=True).exists():
            raise ValidationError('No active students in this group.')
        return group


class StudentExerciseForm(forms.ModelForm):
    points = forms.IntegerField()  # dummy initialisation
    # needed for dynamic initialisation in __init__()

    class Meta:
        model = models.Student
        fields = ('points',)
    
    def __init__(self, *args, **kwargs):
        super(StudentExerciseForm, self).__init__(*args, **kwargs)
        self.fields['points'] = forms.TypedChoiceField(
            required=False,
            choices=[('', '')] + list(models.points_choices()),
            coerce=Decimal)

    def clean(self):
        cleaned_data = super(StudentExerciseForm, self).clean()
        student = self.cleaned_data['id']
        if cleaned_data['points'] != '' and models.Exercise.objects.filter(
            student=student, sheet=self.sheet).exists():
            self._errors['points'] = ErrorList(
                ['Exercise %s for this student already exists.' % self.sheet])
        return cleaned_data

    def save(self, commit=True):
        if self.sheet is None:
            raise ValueError('No sheet given')
        student = self.cleaned_data['id']
        return models.Exercise.objects.create(
            student=student, group=student.group,
            sheet=self.sheet, points=self.cleaned_data['points'])


ExerciseFormSet = modelformset_factory(
    models.Student,
    form=StudentExerciseForm,
    extra=0)


class SheetForm(forms.Form):
    sheet = forms.IntegerField()


class GroupsForm(forms.Form):
    groups = forms.ModelMultipleChoiceField(
        queryset=models.Group.objects.all())
#        widget=HiddenInput)


class QuerySpecialOptForm(forms.Form):
    select_query = forms.ChoiceField(
        choices=(('exam_exercise', 'Exam vs exercise points'),
                 ('exam_subject', 'Exam 1 by subject'),
                 ('exam_first', 'Exam 1 first semester'),
                 ('exam_both', 'both exams'),
                 ('exam_group', 'Exam 1 by group'),
                 ('exgroup_diff', 'Exercise from different group')
            ))
    subject_from = forms.ChoiceField(
        label = "Use subject from",
        choices = (('exam', 'exam record'),
                   ('student', 'student record')
            ))


class ExportEntryTestsForm(forms.Form):
    export_choice = forms.ChoiceField(
        choices=(('all', 'all entry tests'),
                 ('active_missing', 'active students without passed test')
                 ))


class ExportExamResultsForm(forms.Form):
    examnr = forms.ModelChoiceField(
        label='Exam number',
        queryset=models.MasterExam.objects.all())
