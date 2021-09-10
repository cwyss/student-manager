# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Student'
        db.create_table('student_manager_student', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('matrikel', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('student_manager', ['Student'])

        # Adding model 'Exercise'
        db.create_table('student_manager_exercise', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('student', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['student_manager.Student'])),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('points', self.gf('django.db.models.fields.DecimalField')(max_digits=2, decimal_places=1)),
        ))
        db.send_create_signal('student_manager', ['Exercise'])

        # Adding unique constraint on 'Exercise', fields ['student', 'number']
        db.create_unique('student_manager_exercise', ['student_id', 'number'])


    def backwards(self, orm):
        # Removing unique constraint on 'Exercise', fields ['student', 'number']
        db.delete_unique('student_manager_exercise', ['student_id', 'number'])

        # Deleting model 'Student'
        db.delete_table('student_manager_student')

        # Deleting model 'Exercise'
        db.delete_table('student_manager_exercise')


    models = {
        'student_manager.exercise': {
            'Meta': {'ordering': "('student', 'number')", 'unique_together': "(('student', 'number'),)", 'object_name': 'Exercise'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'points': ('django.db.models.fields.DecimalField', [], {'max_digits': '2', 'decimal_places': '1'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.Student']"})
        },
        'student_manager.student': {
            'Meta': {'ordering': "('last_name', 'first_name')", 'object_name': 'Student'},
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'matrikel': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        }
    }

    complete_apps = ['student_manager']