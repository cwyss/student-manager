# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EntryTest',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('result', models.CharField(choices=[('fail', 'fail'), ('pass', 'pass')], max_length=4, null=True, blank=True)),
            ],
            options={
                'ordering': ('student',),
            },
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, null=True, blank=True)),
                ('resit', models.IntegerField(null=True, blank=True)),
                ('points', models.DecimalField(max_digits=3, null=True, blank=True, decimal_places=1)),
                ('number', models.IntegerField(null=True, blank=True)),
                ('exam_group', models.IntegerField(null=True, blank=True)),
                ('mark', models.DecimalField(max_digits=2, null=True, blank=True, decimal_places=1)),
                ('final_mark', models.DecimalField(max_digits=2, null=True, blank=True, decimal_places=1)),
            ],
            options={
                'ordering': ('examnr', 'student'),
            },
        ),
        migrations.CreateModel(
            name='ExamPart',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('points', models.DecimalField(max_digits=3, null=True, blank=True, decimal_places=1)),
                ('exam', models.ForeignKey(to='student_manager.Exam', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('exam', 'number'),
            },
        ),
        migrations.CreateModel(
            name='Exercise',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('sheet', models.IntegerField()),
                ('points', models.DecimalField(decimal_places=2, max_digits=4)),
            ],
            options={
                'ordering': ('student', 'sheet'),
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('time', models.CharField(max_length=200, null=True, blank=True, verbose_name='time / group name (for import regist.)')),
                ('assistent', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'ordering': ('number',),
            },
        ),
        migrations.CreateModel(
            name='MasterExam',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('number', models.IntegerField(unique=True)),
                ('title', models.CharField(max_length=200, null=True, blank=True)),
                ('mark_limits', models.TextField(null=True, blank=True)),
                ('num_exercises', models.IntegerField(default=0)),
                ('max_points', models.IntegerField(null=True, blank=True)),
                ('part_points', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('priority', models.IntegerField(null=True, blank=True)),
                ('status', models.CharField(choices=[('AN', 'AN'), ('ZU', 'ZU'), ('ST', 'ST'), ('HP', 'HP'), ('NP', 'NP')], max_length=2, null=True, blank=True)),
                ('group', models.ForeignKey(to='student_manager.Group', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('group', 'priority'),
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('capacity', models.IntegerField(null=True, blank=True)),
                ('priority', models.IntegerField(null=True, blank=True)),
                ('first_seat', models.IntegerField(null=True, blank=True)),
                ('seat_map', models.TextField(null=True, blank=True)),
                ('examnr', models.ForeignKey(to='student_manager.MasterExam', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('examnr', 'priority'),
            },
        ),
        migrations.CreateModel(
            name='StaticData',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('key', models.CharField(max_length=100)),
                ('value', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Static data',
                'ordering': ('key',),
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('matrikel', models.IntegerField(null=True, blank=True)),
                ('modulo_matrikel', models.IntegerField(null=True, blank=True, verbose_name='modulo')),
                ('obscured_matrikel', models.CharField(max_length=10, null=True, blank=True, verbose_name='obscured')),
                ('last_name', models.CharField(max_length=200, null=True, blank=True)),
                ('first_name', models.CharField(max_length=200, null=True, blank=True)),
                ('subject', models.CharField(max_length=200, null=True, blank=True)),
                ('semester', models.IntegerField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('group', models.ForeignKey(null=True, to='student_manager.Group', on_delete=models.CASCADE, blank=True)),
            ],
            options={
                'ordering': ('last_name', 'first_name'),
            },
        ),
        migrations.AddField(
            model_name='registration',
            name='student',
            field=models.ForeignKey(to='student_manager.Student', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='exercise',
            name='group',
            field=models.ForeignKey(null=True, to='student_manager.Group', on_delete=models.CASCADE, blank=True),
        ),
        migrations.AddField(
            model_name='exercise',
            name='student',
            field=models.ForeignKey(to='student_manager.Student', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='exam',
            name='examnr',
            field=models.ForeignKey(to='student_manager.MasterExam', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='exam',
            name='room',
            field=models.ForeignKey(null=True, to='student_manager.Room', on_delete=models.CASCADE, blank=True),
        ),
        migrations.AddField(
            model_name='exam',
            name='student',
            field=models.ForeignKey(to='student_manager.Student', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='entrytest',
            name='student',
            field=models.ForeignKey(unique=True, to='student_manager.Student', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='registration',
            unique_together=set([('student', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='exercise',
            unique_together=set([('student', 'sheet')]),
        ),
        migrations.AlterUniqueTogether(
            name='exampart',
            unique_together=set([('exam', 'number')]),
        ),
        migrations.AlterUniqueTogether(
            name='exam',
            unique_together=set([('student', 'examnr'), ('examnr', 'number')]),
        ),
    ]
