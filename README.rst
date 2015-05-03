A small Django-based application for managing stutent's exercises, exams etc.


Installation
============

To create the database from scratch, run::

  ./manage.py syncdb --all
  ./manage.py migrate --fake

If $LANG is not set::

  LANG=en_GB.UTF-8 ./manage.py syncdb --all

To update an existing database after a code change::

  ./manage.py migrate

To start the server::

  ./manage.py runserver

Start server with http port different from 8000 (e.g. for two servers running
simultaniously)::

  ./manage.py runserver PORTNUMBER


Usage
=====

static data keys
----------------

lecture::
  lecture name for headings

subject_translation::
  translation from long subject name to short name,
  used for import registration data,
  json dictionary: {"Electrical Engineering": "ET", "Optionalbereich": "Opt"}

bonus1, bonus2::
  minimal points for 1/3, 2/3 bonus on exam mark

maxpoints::
  maximal points over all sheets

sheet_points::
  max points per sheet (default: 5)

points_div::
  divisor for fractional sheet points, i.e. steps of 1/points_div
  (default: 2)

query_exam_pointstep::
  stepsize for grouping exam points

master exam data
----------------

mark_limits::
  list of point-mark-tuples; point is minimum point value for this mark
  list in json format: [[point, mark], ...]
  order by decreasing points

part points::
  list of points of each part of the exam: [points1, points2, ...]
  (used for query exam parts)

import formats
--------------

import student data (CSV)::
  matrikel number
  last name
  first name
  subject
  semester
  group

import exercise data, exercise table (CSV)::
  matrikel number
  sheet number
  points

import exercise data, big table (CSV)::
  matrikel number
  points sheet 1
  points sheet 2
  ...
  points sheet n

import exam data::
  subject line 'subject: <subject>' followed by lines containing::
    number (ignored)
    last name
    first name
    matrikel number
    [more fields, optional, ignored]
    resit count

  If last and/or first name contain more than one first/last name,
  then last name must be separated by two or more spaces.

  Use 'pdftotext -layout anmeldungen.pdf' to create text file from pdf
  while preserving table structure.

import registration data (CSV or Wusel-style XLS)::
  matrikel number
  last name
  first name
  email (ignored)
  subject (translated via static data key subject_translation)
  p version (ignored)
  semester
  status
  priority
  group (translated via group field "time / group name")



Development notes
=================

enter virtualenv::

  workon studmgr

  studmgr: django version 1.4.3
  studmgr2: django version 1.6.5

leave virtualenv::

  deactivate

new fields added to db table; generates migration file::

  ./manage.py schemamigration student_manager --auto
  ./manage.py migrate

create virtualenv::

  mkvirtualenv studmgr
  pip install -r path/to/studmgr/requirements.txt
