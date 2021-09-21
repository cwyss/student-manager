# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student_manager', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entrytest',
            name='student',
            field=models.OneToOneField(to='student_manager.Student'),
        ),
    ]
