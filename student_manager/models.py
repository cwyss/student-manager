"""The models for mapping database tables to Django objects."""

from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max
from django.core.exceptions import ValidationError


POINTS_CHOICES = [(i/2.0, str(i/2.0)) for i in range(11)]
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


class Student(models.Model):
    matrikel = models.IntegerField(null=True, blank=True)
    obscured_matrikel = models.CharField(max_length=10, null=True, blank=True)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    first_name = models.CharField(max_length=200, null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    group = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s, %s (%s)' % (self.last_name, self.first_name, self.matrikel)

    def number_of_exercises(self):
        return self.exercise_set.count()

    number_of_exercises.short_description = 'Exercises'

    def total_points(self):
        total = self.exercise_set.aggregate(Sum('points'))['points__sum']
        return total or Decimal('0.0')

    def bonus(self):
        return '1/3'

    def save(self, *args, **kwargs):
        validate_matrikel(self.matrikel, self.id)
        if self.matrikel and not self.obscured_matrikel:
            self.obscured_matrikel = str(self.matrikel)[-4:]
                
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
        return '%i: %1.1f - %s' % (self.sheet, self.points, self.student)

    def save(self, *args, **kwargs):
        if float(self.points) not in VALID_POINTS:
            raise ValidationError('invalid point value')
        return super(Exercise, self).save(*args, **kwargs)

    @classmethod
    def total_num_exercises(cls):
        return cls.objects.aggregate(total=Max('sheet'))['total'] or 0

