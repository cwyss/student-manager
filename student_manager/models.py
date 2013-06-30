"""The models for mapping database tables to Django objects."""

from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max


POINTS_CHOICES = [(i/2.0, str(i/2.0)) for i in range(11)]


class Student(models.Model):
    matrikel = models.IntegerField(null=True, blank=True)
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

    def total_points(self):
        total = self.exercise_set.aggregate(Sum('points'))['points__sum']
        return total or Decimal('0.0')

    class Meta:
        ordering = ('last_name', 'first_name')


class Exercise(models.Model):
    student = models.ForeignKey(Student)
    group = models.IntegerField(null=True, blank=True)
    number = models.IntegerField()
    points = models.DecimalField(max_digits=2, decimal_places=1,
                                 choices=POINTS_CHOICES)

    class Meta:
        unique_together = (('student', 'number'),)
        ordering = ('student', 'number')

    def __unicode__(self):
        return '%i: %1.1f - %s' % (self.number, self.points, self.student)

    @classmethod
    def total_num_exercises(cls):
        return cls.objects.aggregate(total=Max('number'))['total']
