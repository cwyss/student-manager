"""Template tags for the student manager app."""

from django import template
from student_manager import models

register = template.Library()


def static_data(key):
    try:
        data = models.StaticData.objects.get(key=key)
        return str(data.value)
    except models.StaticData.DoesNotExist:
        return ''

register.simple_tag(static_data)
