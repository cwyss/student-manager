# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Exercise', fields ['number', 'student']
        db.delete_unique('student_manager_exercise', ['number', 'student_id'])

        # Deleting field 'Exercise.number'
        db.delete_column('student_manager_exercise', 'number')

        # Adding field 'Exercise.sheet'
        db.add_column('student_manager_exercise', 'sheet',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Adding unique constraint on 'Exercise', fields ['sheet', 'student']
        db.create_unique('student_manager_exercise', ['sheet', 'student_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Exercise', fields ['sheet', 'student']
        db.delete_unique('student_manager_exercise', ['sheet', 'student_id'])


        # User chose to not deal with backwards NULL issues for 'Exercise.number'
        raise RuntimeError("Cannot reverse this migration. 'Exercise.number' and its values cannot be restored.")
        # Deleting field 'Exercise.sheet'
        db.delete_column('student_manager_exercise', 'sheet')

        # Adding unique constraint on 'Exercise', fields ['number', 'student']
        db.create_unique('student_manager_exercise', ['number', 'student_id'])


    models = {
        'student_manager.exercise': {
            'Meta': {'ordering': "('student', 'sheet')", 'unique_together': "(('student', 'sheet'),)", 'object_name': 'Exercise'},
            'group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.DecimalField', [], {'max_digits': '2', 'decimal_places': '1'}),
            'sheet': ('django.db.models.fields.IntegerField', [], {}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.Student']"})
        },
        'student_manager.student': {
            'Meta': {'ordering': "('last_name', 'first_name')", 'object_name': 'Student'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'matrikel': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'semester': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['student_manager']