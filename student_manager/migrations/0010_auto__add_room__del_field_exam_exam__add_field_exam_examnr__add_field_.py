# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Exam', fields ['exam', 'student']
        db.delete_unique('student_manager_exam', ['exam', 'student_id'])

        # Adding model 'Room'
        db.create_table('student_manager_room', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('examnr', self.gf('django.db.models.fields.IntegerField')()),
            ('capacity', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('student_manager', ['Room'])

        # Deleting field 'Exam.exam'
        db.delete_column('student_manager_exam', 'exam')

        # Adding field 'Exam.examnr'
        db.add_column('student_manager_exam', 'examnr',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Exam.room'
        db.add_column('student_manager_exam', 'room',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['student_manager.Room'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'Exam.number'
        db.add_column('student_manager_exam', 'number',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding unique constraint on 'Exam', fields ['examnr', 'student']
        db.create_unique('student_manager_exam', ['examnr', 'student_id'])

        # Adding unique constraint on 'Exam', fields ['examnr', 'number']
        db.create_unique('student_manager_exam', ['examnr', 'number'])


    def backwards(self, orm):
        # Removing unique constraint on 'Exam', fields ['examnr', 'number']
        db.delete_unique('student_manager_exam', ['examnr', 'number'])

        # Removing unique constraint on 'Exam', fields ['examnr', 'student']
        db.delete_unique('student_manager_exam', ['examnr', 'student_id'])

        # Deleting model 'Room'
        db.delete_table('student_manager_room')


        # User chose to not deal with backwards NULL issues for 'Exam.exam'
        raise RuntimeError("Cannot reverse this migration. 'Exam.exam' and its values cannot be restored.")
        # Deleting field 'Exam.examnr'
        db.delete_column('student_manager_exam', 'examnr')

        # Deleting field 'Exam.room'
        db.delete_column('student_manager_exam', 'room_id')

        # Deleting field 'Exam.number'
        db.delete_column('student_manager_exam', 'number')

        # Adding unique constraint on 'Exam', fields ['exam', 'student']
        db.create_unique('student_manager_exam', ['exam', 'student_id'])


    models = {
        'student_manager.exam': {
            'Meta': {'ordering': "('examnr', 'student')", 'unique_together': "(('student', 'examnr'), ('examnr', 'number'))", 'object_name': 'Exam'},
            'examnr': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'points': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '3', 'decimal_places': '1', 'blank': 'True'}),
            'resit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.Room']", 'null': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.Student']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'student_manager.exercise': {
            'Meta': {'ordering': "('student', 'sheet')", 'unique_together': "(('student', 'sheet'),)", 'object_name': 'Exercise'},
            'group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.DecimalField', [], {'max_digits': '2', 'decimal_places': '1'}),
            'sheet': ('django.db.models.fields.IntegerField', [], {}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.Student']"})
        },
        'student_manager.room': {
            'Meta': {'ordering': "('examnr', 'priority')", 'object_name': 'Room'},
            'capacity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'examnr': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'student_manager.student': {
            'Meta': {'ordering': "('last_name', 'first_name')", 'object_name': 'Student'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'matrikel': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'modulo_matrikel': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'obscured_matrikel': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'semester': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['student_manager']