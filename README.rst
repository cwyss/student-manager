A small Django-based application for managing stutent's exercises, exams etc.


Installation
============

To create the database from scratch, run::

  ./manage.py migrate
  ./manage.py createsuperuser

To update an existing database after a code change::

  ./manage.py migrate

To migrate an old database (i.e. with django 1.6 migrations)
to django 1.8::
  
  ./manage.py migrate --fake-initial
  
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

require_etest::
  if this key exists, passed entry tests are checked for bonus
  
master exam data
----------------

mark_limits::
  list of point-mark-tuples; point is minimum point value for this mark
  list in json format: [[point, mark], ...]
  order by decreasing points

part points::
  list of points of each part of the exam: [points1, points2, ...]
  (used for query exam parts)

room data
---------

seat_map::
  list of seat numbers [seatnr1, seatnr2, ...]
  used only if first_seat also given; exam.number - first_seat is the
  index into the seat_map
  
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

  empty point field or '-': no exercise for this sheet
  
import exercise data, big table with group entry (CSV)::
  matrikel number
  group
  points sheet 1
  points sheet 2
  ...
  points sheet n

import exam data::
  subject line 'subject: <subject>' followed by lines containing the following fields::
    number (ignored)
    last name
    first name
    matrikel number
    [more fields, optional, ignored]
    resit count [optional: if there are one or more fields after the matrikel number,
      then the last field is interpreted as the resit count]

  Entries are in CSV style, separated by a separation character.
  Empty lines are ignored.
  
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

import entry test data (CSV)::
  matrikel number
  test result::
    one of 'bestanden', 'nicht bestanden', 'pass', 'fail'
    an empty result or '-' are ignored (=> no test created)
  
  

Development notes
=================

new fields added to db table; generates migration file::

  ./manage.py makemigrations
  ./manage.py migrate


virtualenvironment setup: venv
------------------------------

create::
  python3 -m venv path/to/venvs/studmgr

activate::
  source path/to/venvs/studmgr/bin/activate

setup::
  pip install -r requirements.txt

leave::
  deactivate


virtualenvwrapper (obsolte)
---------------------------

enter virtualenv::

  workon studmgr

  studmgr: django version 1.4.3
  studmgr2: django version 1.6.5
  studmgr3: django version 1.8.19  (with python 3.7)

  studmgr-dj1.9: django 1.9.13
  studmgr-dj1.10: django 1.10.8
  studmgr-dj1.11: django 1.11.29
  studmgr-dj2.0: django 2.0.13
  studmgr-dj2.1: django 2.1.15
  studmgr-dj2.2: django 2.2.24

leave virtualenv::

  deactivate

create virtualenv::

  mkvirtualenv -p /usr/bin/python3 studmgr         # use python3
  pip install -r path/to/studmgr/requirements.txt
