A small Django-based application for managing stutent's exercises, exams etc.


Installation
============

To create the database from scratch, run::

  ./manage.py syncdb --all
  ./manage.py migrate --fake

To update an existing database after a code change::

  ./manage.py migrate

To start the server::

  ./manage.py runserver
