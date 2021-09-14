"""The models for mapping database tables to Django objects."""

from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

import json


class StaticData(models.Model):
    key = models.CharField(max_length=100)
    value = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('key',)
        verbose_name_plural = 'Static data'

    def __str__(self):
        return '%s' % self.key

    @classmethod
    def get_key(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def get_subject_transl(cls):
        try:
            jstr = cls.objects.get(key='subject_translation').value
            jstr = jstr.translate({0xa0: 32})
            transl = json.loads(jstr)
            return transl
        except cls.DoesNotExist:
            return {}

    @classmethod
    def get_sheet_points(cls):
        return int(cls.get_key('sheet_points', 5))

    @classmethod
    def get_points_div(cls):
        return int(cls.get_key('points_div', 2))

    @classmethod
    def get_lecture_name(cls):
        return cls.get_key('lecture')


class Group(models.Model):
    number = models.IntegerField()
    time = models.CharField("time / group name (for import regist.)",
                            max_length=200, null=True, blank=True)
    assistent = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return '%d' % self.number

    class Meta:
        ordering = ('number',)

    @classmethod
    def get_group(cls, number, create=False):
        try:
            group = cls.objects.get(number=number)
        except cls.DoesNotExist:
            if create:
                group = cls.objects.create(number=number)
            else:
                group = None
        return group

    @classmethod
    def get_group_transl(cls, groups, create=False):
        if cls.objects.count()>0:
            max_group_number = \
                cls.objects.aggregate(Max('number'))['number__max']
        else:
            max_group_number = 0
        grp_transl = {}
        for grpstr in groups:
            try:
                group = cls.objects.get(time=grpstr)
            except cls.DoesNotExist:
                if create:
                    max_group_number +=  1
                    group = cls.objects.create(number=max_group_number,
                                               time=grpstr)
                else:
                    group = None
            if group:
                grp_transl[grpstr] = group
        return grp_transl


def validate_matrikel(matrikel, student_id):
    if matrikel:
        query = Student.objects.filter(matrikel=matrikel)
    else:
        query = Student.objects.none()
    if student_id:
        query = query.exclude(id=student_id)
    if query.exists():
        raise ValidationError('Matrikel already exists.')


class StudentManager(models.Manager):
    """ manager used in Student model """
    def get_queryset(self):
        """ make Student total_points field, by which we can order """
        query = super(StudentManager, self).get_queryset()
        return query.annotate(_total_points=Sum('exercise__points'))

    def get_pure_queryset(self):
        """ get query set without annotation/join;
        needed for queries to count e.g. students by semester """
        return super(StudentManager, self).get_queryset()


class Student(models.Model):
    matrikel = models.IntegerField(null=True, blank=True)
    modulo_matrikel = models.IntegerField(null=True, blank=True,
                                          verbose_name='modulo')
    obscured_matrikel = models.CharField(max_length=10, null=True, blank=True,
                                         verbose_name='obscured')
    last_name = models.CharField(max_length=200, null=True, blank=True)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)
    active = models.BooleanField(default=True)

    objects = StudentManager()

    def __str__(self):
        return '%s, %s (%s)' % (self.last_name, self.first_name, self.matrikel)

    def number_of_exercises(self):
        return self.exercise_set.count()

    number_of_exercises.short_description = 'Exercises'

    def total_points(self, force_recalc=False):
        if hasattr(self, '_total_points') and not force_recalc:
            _total_points = self._total_points
        else:
            _total_points = self.exercise_set.aggregate(
                Sum('points'))['points__sum']
        return _total_points or Decimal('0.0')
    
    total_points.admin_order_field = '_total_points'

    def bonus(self, force_recalc=False):
        try:
            bonus1 = Decimal(StaticData.objects.get(key='bonus1').value)
            bonus2 = Decimal(StaticData.objects.get(key='bonus2').value)
        except StaticData.DoesNotExist:
            bonus1 = None
        try:
            StaticData.objects.get(key='require_etest')
            etest = True
        except StaticData.DoesNotExist:
            etest = False

        if not etest and not bonus1:
            return None
        if etest:
            if self.entrytest_set.exists():
                etest = self.entrytest_set.get()
                if etest.result=='fail':
                    return 'etest fail'
            else:
                return 'no etest'
        if bonus1:
            total = self.total_points(force_recalc)
            if total>=bonus2:
                return '2/3'
            elif total>=bonus1:
                return '1/3'

        return ''

    def save(self, *args, **kwargs):
        validate_matrikel(self.matrikel, self.id)
        if self.matrikel:
            self.modulo_matrikel = int(str(self.matrikel)[-4:])
        if self.matrikel and not self.obscured_matrikel:
            self.obscured_matrikel = '%04d' % self.modulo_matrikel
        return super(Student, self).save(*args, **kwargs)

    class Meta:
        ordering = ('last_name', 'first_name')


def points_choices():
    max_points = StaticData.get_sheet_points()
    points_div = StaticData.get_points_div()
    n = max_points * points_div + 1
    for i in range(n):
        choice = (Decimal(i)/points_div, str(float(i)/points_div))
        yield choice

def valid_points():
    for (val, lbl) in points_choices():
        yield val


class Exercise(models.Model):
    student = models.ForeignKey(Student)
    group = models.ForeignKey(Group, null=True, blank=True)
    sheet = models.IntegerField()
    points = models.DecimalField(
        max_digits=4, decimal_places=2)

    class Meta:
        unique_together = (('student', 'sheet'),)
        ordering = ('student', 'sheet')

    def __str__(self):
        return '%i: %1.1f - %s' % (self.sheet, self.points, self.student)

    def save(self, *args, **kwargs):
        if float(self.points) not in valid_points():
            raise ValidationError('invalid point value')
        return super(Exercise, self).save(*args, **kwargs)

    @classmethod
    def total_num_exercises(cls):
        return cls.objects.aggregate(total=Max('sheet'))['total'] or 0

@receiver(post_save, sender=Exercise)
def update_mark_from_exercise(sender, **kwargs):
    exercise = kwargs['instance']
    for exam in exercise.student.exam_set.all():
        exam.save(
            force_recalc=True  # trigger recalculation of bonus in student model
        )


class MasterExam(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    mark_limits = models.TextField(null=True, blank=True)
    num_exercises = models.IntegerField(default=0)
    max_points = models.IntegerField(null=True, blank=True)
    part_points = models.TextField(null=True, blank=True)

    def __str__(self):
        return '%s' % self.number

@receiver(post_save, sender=MasterExam)
def update_mark_from_masterexam(sender, **kwargs):
    masterexam = kwargs['instance']
    for exam in masterexam.exam_set.all():
        exam.save()


class Room(models.Model):
    name = models.CharField(max_length=200)
    examnr = models.ForeignKey(MasterExam)
    capacity = models.IntegerField(null=True, blank=True)
    priority = models.IntegerField(null=True, blank=True)
    first_seat = models.IntegerField(null=True, blank=True)
    seat_map = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ('examnr', 'priority')

    def __str__(self):
        return '%s (%d)' % (self.name, self.examnr.number)


BONUSMAP = {5.0: 5.0, 4.0: 3.7, 3.7: 3.3, 3.3: 3.0, 3.0: 2.7,
            2.7: 2.3, 2.3: 2.0, 2.0: 1.7, 1.7: 1.3, 1.3: 1.0,
            1.0: 1.0}

class Exam(models.Model):
    student = models.ForeignKey(Student)
    subject = models.CharField(max_length=200, null=True, blank=True)
    examnr = models.ForeignKey(MasterExam)
    resit = models.IntegerField(null=True, blank=True)
    points = models.DecimalField(max_digits=3, decimal_places=1, 
                                 null=True, blank=True)
    room = models.ForeignKey(Room, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    exam_group = models.IntegerField(null=True, blank=True)
    mark = models.DecimalField(max_digits=2, decimal_places=1,
                               null=True, blank=True)
    final_mark = models.DecimalField(max_digits=2, decimal_places=1,
                                     null=True, blank=True)

    class Meta:
        unique_together = (('student', 'examnr'),
                           ('examnr','number'))
        ordering = ('examnr', 'student')

    def __str__(self):
        return '%i: %s' % (self.examnr.number, self.student)

    def save(self, *args, **kwargs):
        if self.examnr.mark_limits and self.points != None:
            mark_limits = json.loads(self.examnr.mark_limits)
            for limit,mark in mark_limits:
                if self.points >= limit:
                    self.mark = mark
                    break

            force_recalc = kwargs.pop('force_recalc', False)
            bonus = self.student.bonus(force_recalc)
            if bonus == '1/3':
                self.final_mark = BONUSMAP[self.mark]
            elif bonus == '2/3':
                self.final_mark = BONUSMAP[BONUSMAP[self.mark]]
            else:
                self.final_mark = self.mark
        else:
            self.mark = None
            self.final_mark = None
        return super(Exam, self).save(*args, **kwargs)


class ExamPart(models.Model):
    exam = models.ForeignKey(Exam)
    number = models.IntegerField()
    points = models.DecimalField(max_digits=3, decimal_places=1, 
                                 null=True, blank=True)

    class Meta:
        ordering = ('exam', 'number')
        unique_together = (('exam', 'number'),)

    def __str__(self):
        return '%i(%i): %s' % (self.exam.examnr.number, self.number,
                                self.exam.student)


class Registration(models.Model):
    student = models.ForeignKey(Student)
    group = models.ForeignKey(Group)
    priority = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=2, null=True, blank=True,
                              choices=[('AN','AN'),('ZU','ZU'),
                                       ('ST','ST'),
                                       ('HP','HP'),('NP','NP')])

    def assigned_group(self):
        return self.student.group

    assigned_group.short_description = 'assigned'

    class Meta:
        ordering = ('group','priority')
        unique_together = (('student','group'),)

    def __str__(self):
        return '%s: %d %s' % (self.student, self.group.number, self.status)


class EntryTest(models.Model):
    student = models.ForeignKey(Student, unique=True)
    result = models.CharField(max_length=4, null=True, blank=True,
                              choices=[('fail','fail'),('pass','pass')])

    class Meta:
        ordering = ('student',)
        
    def __str__(self):
        return '%s: %s' % (self.student, self.result)
