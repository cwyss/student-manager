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


CSV import formats
==================

import student data::

import exercise data, exercise table::

  matrikel number
  sheet number
  points

import exercise data, big table::

  matrikel number
  points sheet 1
  points sheet 2
  ...
  points sheet n


Development notes
=================

enter virtualenv::

  workon studmgr

leave virtualenv::

  deactivate

new fields added to db table; generates migration file::

  ./manage.py schemamigration student_manager --auto
  ./manage.py migrate
