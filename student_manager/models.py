"""The models for mapping database tables to Django objects."""

from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max
from django.core.exceptions import ValidationError
import json


POINTS_CHOICES = [(i/Decimal('2'), str(i/2.0)) for i in range(11)]
VALID_POINTS = [x[0] for x in POINTS_CHOICES]

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
    def get_query_set(self):
        query = super(StudentManager, self).get_query_set()
        return query.annotate(_total_points=Sum('exercise__points'))


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
    group = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)

    objects = StudentManager()

    def __unicode__(self):
        return u'%s, %s (%s)' % (self.last_name, self.first_name, self.matrikel)

    def number_of_exercises(self):
        return self.exercise_set.count()

    number_of_exercises.short_description = 'Exercises'

    def total_points(self):
        if hasattr(self, '_total_points'):
            _total_points = self._total_points
        else:
            _total_points = self.exercise_set.aggregate(
                Sum('points'))['points__sum']
        return _total_points or Decimal('0.0')
    
    total_points.admin_order_field = '_total_points'

    def bonus(self):
        try:
            bonus1 = Decimal(StaticData.objects.get(key='bonus1').value)
            bonus2 = Decimal(StaticData.objects.get(key='bonus2').value)
        except StaticData.DoesNotExist:
            return None
        total = self.total_points()
        if total>=bonus2:
            return '2/3'
        elif total>=bonus1:
            return '1/3'
        else:
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


class Exercise(models.Model):
    student = models.ForeignKey(Student)
    group = models.IntegerField(null=True, blank=True)
    sheet = models.IntegerField()
    points = models.DecimalField(
        max_digits=2, decimal_places=1,
        choices=POINTS_CHOICES)

    class Meta:
        unique_together = (('student', 'sheet'),)
        ordering = ('student', 'sheet')

    def __unicode__(self):
        return u'%i: %1.1f - %s' % (self.sheet, self.points, self.student)

    def save(self, *args, **kwargs):
        if float(self.points) not in VALID_POINTS:
            raise ValidationError('invalid point value')
        return super(Exercise, self).save(*args, **kwargs)

    @classmethod
    def total_num_exercises(cls):
        return cls.objects.aggregate(total=Max('sheet'))['total'] or 0


class MasterExam(models.Model):
    number = models.IntegerField(unique=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    mark_limits = models.TextField(null=True, blank=True)
    num_exercises = models.IntegerField(default=0)
    max_points = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.number


class Room(models.Model):
    name = models.CharField(max_length=200)
    examnr = models.ForeignKey(MasterExam)
    capacity = models.IntegerField(null=True, blank=True)
    priority = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ('examnr', 'priority')

    def __unicode__(self):
        return u'%s (%d)' % (self.name, self.examnr.number)


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
    mark = models.DecimalField(max_digits=2, decimal_places=1,
                               null=True, blank=True)
    final_mark = models.DecimalField(max_digits=2, decimal_places=1,
                                     null=True, blank=True)

    class Meta:
        unique_together = (('student', 'examnr'),
                           ('examnr','number'))
        ordering = ('examnr', 'student')

    def __unicode__(self):
        return u'%i: %s' % (self.examnr.number, self.student)

    def save(self, *args, **kwargs):
        if self.examnr.mark_limits and self.points != None:
            mark_limits = json.loads(self.examnr.mark_limits)
            for limit,mark in mark_limits:
                if self.points >= limit:
                    self.mark = mark
                    break
            if self.student.bonus() == '1/3':
                self.final_mark = BONUSMAP[self.mark]
            elif self.student.bonus() == '2/3':
                self.final_mark = BONUSMAP[BONUSMAP[self.mark]]
            else:
                self.final_mark = self.mark
        else:
            self.mark = None
            self.final_mark = None
        return super(Exam, self).save(*args, **kwargs)


def make_translation_dict(jstr):
    try:
        jstr = jstr.translate({0xa0: 32})
        transl = json.loads(jstr)
        return transl
    except cls.DoesNotExist:
            return {}

class StaticData(models.Model):
    key = models.CharField(max_length=100)
    value = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('key',)
        verbose_name_plural = 'Static data'

    def __unicode__(self):
        return u'%s' % self.key

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
    def get_group_transl(cls):
        try:
            jstr = cls.objects.get(key='group_translation').value
            jstr = jstr.translate({0xa0: 32})
            transl = json.loads(jstr)
            return transl
        except cls.DoesNotExist:
            return {}

    @classmethod
    def update_group_transl(cls, groups):
        grp_transl = cls.get_group_transl()
        if len(grp_transl)>0:
            grpcnt = max(grp_transl.values())
        else:
            grpcnt = 0
        for grpstr in groups:
            if not grp_transl.has_key(grpstr):
                grpcnt += 1
                grp_transl[grpstr] = grpcnt
        transl_list = grp_transl.items()
        transl_list.sort(key=lambda x:x[1])
        transl_str = '{'
        transl_str += ',\n'.join(['"%s": %d' % item for item in transl_list])
        transl_str += '}'
        try:
            transl_data = cls.objects.get(key='group_translation')
        except cls.DoesNotExist:
            transl_data = cls(key='group_translation')
        transl_data.value = transl_str
        transl_data.save()


class Registration(models.Model):
    student = models.ForeignKey(Student)
    group = models.IntegerField()
    priority = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=2, null=True, blank=True,
                              choices=[(u'AN','AN'),(u'ZU','ZU'),
                                       (u'ST','ST'),
                                       (u'HP','HP'),(u'NP','NP')])
                                       

    def assigned_group(self):
        return self.student.group

    assigned_group.short_description = 'assigned'

    class Meta:
        ordering = ('group','priority')
        unique_together = (('student','group'),)

    def __unicode__(self):
        return u'%s: %d %s' % (self.student, self.group, self.status)

