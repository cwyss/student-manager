"""Forms."""

from django import forms
from django.forms.models import modelformset_factory
from django.utils.translation import ugettext_lazy as _

from student_manager import models


class StudentForm(forms.ModelForm):

    class Meta:
        model = models.Student
        exclude = ('modulo_matrikel',)

    def clean_matrikel(self):
        student_id = self.instance.id  if self.instance else None
        matrikel = self.cleaned_data['matrikel']
        models.validate_matrikel(matrikel, student_id)
        return matrikel


class ExamForm(forms.ModelForm):

    class Meta:
        model = models.Exam
        fields = ('points',)

        
ExamFormSet = modelformset_factory(models.Exam, form=ExamForm, extra=0)


class ImportExercisesForm(forms.Form):
    group = forms.IntegerField()
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))
    format = forms.ChoiceField(choices=(
            ('', 'Please select'),
            (1, 'Exercise table (one entry per exercise)'),
            (2, 'Big table (one column per sheet)')))


class ImportStudentsForm(forms.Form):
    column_separator = forms.CharField(max_length=1, initial=';')
    csv_file = forms.FileField(label=_('CSV file'))


class PrintStudentsOptForm(forms.Form):
    matrikel = forms.ChoiceField(label=_('Selection'),
                                 choices=(('on', 'Students with matrikel'),
                                          ('', 'Students without matrikel')),
                                 initial='on')
    total = forms.BooleanField(label=_('Display total/bonus columns'))


class ImportExamsForm(forms.Form):
    examnr = forms.ChoiceField(label='Exam number', 
                             choices=((1, '1'), (2, '2')))
    file = forms.FileField(label=_('File'))


class PrintExamsOptForm(forms.Form):
    examnr = forms.ChoiceField(label='Exam number', 
                             choices=((1, '1'), (2, '2')))

    
