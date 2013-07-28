# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Exam.mark'
        db.add_column('student_manager_exam', 'mark',
                      self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=2, decimal_places=1, blank=True),
                      keep_default=False)

        # Adding field 'Exam.endmark'
        db.add_column('student_manager_exam', 'endmark',
                      self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=2, decimal_places=1, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Exam.mark'
        db.delete_column('student_manager_exam', 'mark')

        # Deleting field 'Exam.endmark'
        db.delete_column('student_manager_exam', 'endmark')


    models = {
        'student_manager.exam': {
            'Meta': {'ordering': "('examnr', 'student')", 'unique_together': "(('student', 'examnr'), ('examnr', 'number'))", 'object_name': 'Exam'},
            'endmark': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '2', 'decimal_places': '1', 'blank': 'True'}),
            'examnr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.MasterExam']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mark': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '2', 'decimal_places': '1', 'blank': 'True'}),
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
        'student_manager.masterexam': {
            'Meta': {'object_name': 'MasterExam'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mark_limits': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'num_exercises': ('django.db.models.fields.IntegerField', [], {}),
            'number': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'student_manager.room': {
            'Meta': {'ordering': "('examnr', 'priority')", 'object_name': 'Room'},
            'capacity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'examnr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student_manager.MasterExam']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'student_manager.staticdata': {
            'Meta': {'ordering': "('key',)", 'object_name': 'StaticData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
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