

from django.db.models.signals import post_save
from django.dispatch import receiver

from student_manager import models


@receiver(post_save, sender=models.MasterExam)
def update_mark_from_masterexam(sender, **kwargs):
    masterexam = kwargs['instance']
    for exam in masterexam.exam_set.all():
        exam.save()


@receiver(post_save, sender=models.Exercise)
def update_mark_from_exercise(sender, **kwargs):
    exercise = kwargs['instance']
    for exam in exercise.student.exam_set.all():
        exam.save()
