"""Forms."""

from decimal import Decimal
import json
from django import forms
from django.forms.util import ErrorList
from django.forms.models import (
    modelformset_factory,
    modelform_factory,
    BaseModelFormSet)
from django.forms.widgets import HiddenInput, TextInput
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from student_manager import models


class GroupForm(forms.ModelForm):
    class Meta:
        model = models.Group

    def clean_time(self):
        time = self.cleaned_data['time']
        return time.translate({0xa0: 32})


class StudentForm(forms.ModelForm):
    class Meta:
        model = models.Student
        exclude = ('modulo_matrikel',)

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        models.validate_matrikel(matrikel, student_id)
        return matrikel


class StaticDataForm(forms.ModelForm):
    class Meta:
        model = models.StaticData

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


class MasterExamForm(forms.ModelForm):
    class Meta:
        model = models.MasterExam

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
    group = forms.ModelChoiceField(
        queryset=models.Group.objects.all())
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))
    format = forms.ChoiceField(choices=(
            ('', 'Please select'),
            ('exerc', 'Exercise table (one entry per exercise)'),
            ('sheet', 'Big table (one column per sheet)')))


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
        queryset=models.Group.objects.all())
    total = forms.BooleanField(label=_('Display total/bonus columns'))
    exclude = forms.ChoiceField(
        choices=(('empty', 'Exclude students without exercises'),
                 ('inactive', 'Exclude inactive students')),
        initial='inactive')


class PrintStudentsOptForm(forms.Form):
    order_by = forms.ChoiceField(choices=(('matrikel', 'matrikel number'),
                                          ('name', 'name')))


class ImportExamsForm(forms.Form):
    examnr = forms.ModelChoiceField(
        label='Exam number',
        queryset=models.MasterExam.objects.all())
    file = forms.FileField(label=_('File'))


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


class QueryStudentsOptForm(forms.Form):
    first_field = forms.ChoiceField(
        choices=(('subject', 'Subject'),
                 ('semester', 'Semester'),
                 ('group', 'Group'),
                 ('active', 'Active')))
    second_field = forms.ChoiceField(
        choices=((None, 'None'),
                 ('subject', 'Subject'),
                 ('semester', 'Semester'),
                 ('group', 'Group'),
                 ('active', 'Active')))
    only_active = forms.BooleanField(label=_('Include only active students'),
                                     initial=True)


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
    points = forms.TypedChoiceField(
        required=False,
        choices=[('', '')] + models.POINTS_CHOICES,
        coerce=Decimal)

    class Meta:
        model = models.Student
        fields = ('points',)

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
