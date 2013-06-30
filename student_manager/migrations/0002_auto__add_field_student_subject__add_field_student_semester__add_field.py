# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Student', fields ['matrikel']
        db.delete_unique('student_manager_student', ['matrikel'])

        # Adding field 'Student.subject'
        db.add_column('student_manager_student', 'subject',
                      self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Student.semester'
        db.add_column('student_manager_student', 'semester',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Student.group'
        db.add_column('student_manager_student', 'group',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Student.active'
        db.add_column('student_manager_student', 'active',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


        # Changing field 'Student.first_name'
        db.alter_column('student_manager_student', 'first_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True))

        # Changing field 'Student.last_name'
        db.alter_column('student_manager_student', 'last_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True))

        # Changing field 'Student.matrikel'
        db.alter_column('student_manager_student', 'matrikel', self.gf('django.db.models.fields.IntegerField')(null=True))

    def backwards(self, orm):
        # Deleting field 'Student.subject'
        db.delete_column('student_manager_student', 'subject')

        # Deleting field 'Student.semester'
        db.delete_column('student_manager_student', 'semester')

        # Deleting field 'Student.group'
        db.delete_column('student_manager_student', 'group')

        # Deleting field 'Student.active'
        db.delete_column('student_manager_student', 'active')


        # User chose to not deal with backwards NULL issues for 'Student.first_name'
        raise RuntimeError("Cannot reverse this migration. 'Student.first_name' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Student.last_name'
        raise RuntimeError("Cannot reverse this migration. 'Student.last_name' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Student.matrikel'
        raise RuntimeError("Cannot reverse this migration. 'Student.matrikel' and its values cannot be restored.")
        # Adding unique constraint on 'Student', fields ['matrikel']
        db.create_unique('student_manager_student', ['matrikel'])


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