"""The models for mapping database tables to Django objects."""

from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max
from django.core.exceptions import ValidationError


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
        return self._total_points or Decimal('0.0')
    
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
    num_exercises = models.IntegerField()

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


class Exam(models.Model):
    student = models.ForeignKey(Student)
    subject = models.CharField(max_length=200, null=True, blank=True)
    examnr = models.ForeignKey(MasterExam)
    resit = models.IntegerField(null=True, blank=True)
    points = models.DecimalField(max_digits=3, decimal_places=1, 
                                 null=True, blank=True)
    room = models.ForeignKey(Room, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = (('student', 'examnr'),
                           ('examnr','number'))
        ordering = ('examnr', 'student')

    def __unicode__(self):
        return u'%i: %s' % (self.examnr.number, self.student)


class StaticData(models.Model):
    key = models.CharField(max_length=100)
    value = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('key',)
        verbose_name_plural = 'Static data'

    def __unicode__(self):
        return u'%s' % self.key

