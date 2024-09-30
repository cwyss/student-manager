#!/usr/bin/env python3

import csv, sys


def find_examcsv_fields(row):
    try:
        name_field = row.index('Nachname')
        first_name_field = row.index('Vorname')
        matrikel_field = row.index('Matrikelnummer')
        return {
            'name': name_field,
            'firstname': first_name_field,
            'matrikel': matrikel_field
        }
    except ValueError:
        raise Exception("Exam results file: Column names not recognised") from None

def read_sl_examresult_csv(fname):
    csvfile = open(fname, newline='')
    reader = csv.reader(csvfile, delimiter=';')

    fields = None
    try:
        while not fields:
            row = next(reader)
            if row[0]=='startHISsheet':
                row = next(reader)
                fields = find_examcsv_fields(row)
    except (StopIteration, IndexError):
        raise Exception("Exam results file: HIS csv table not found") from None

    examresults = []
    for row in reader:
        if row[0]=='endHISsheet':
            break
        examresults.append([row[fields['name']], row[fields['firstname']],
                            int(row[fields['matrikel']]), None])

    return examresults


def read_marks_csv(fname):
    csvfile = open(fname, newline='')
    reader = csv.reader(csvfile, delimiter=';')
    next(reader)   # skip header

    marks = {}
    for row in reader:
        matrikel = int(row[0])
        mark = row[3]
        marks[matrikel] = mark

    return marks


def add_marks(examresults, marks):
    missing = []   # matrikel numbers in examresults without corresp. marks

    for exam in examresults:
        try:
            exam[3] = marks[exam[2]]
        except KeyError as err:
            missing.append(err.args[0])
            exam[3] = ''

    return missing


def print_examresults(examresults):
    print("Nachname;Vorname;Matrikelnummer;Leistung")
    for exam in examresults:
        row = (exam[0],exam[1],str(exam[2]),exam[3])
        print(';'.join(row))



if len(sys.argv)!=3:
    print(
"""Usage: merge-exam-marks.py EXAMS MARKS
Merge exam results with participants file from studilöwe

EXAMS: csv file with exam's participants, exported from studilöwe,
       required fields 'Nachname','Vorname','Matrikelnummer'
MARKS: csv file with exam results (marks), as exported from student manager
       (field 1 Matrikelnummer, field 4 mark)

Merged list is printed in csv format to stdout, in the same order
as in the EXAMS file."""
        , file = sys.stderr)
else:
    exams_file = sys.argv[1]
    marks_file = sys.argv[2]

    examresults = read_sl_examresult_csv(exams_file)
    marks = read_marks_csv(marks_file)
    missing = add_marks(examresults, marks)

    print_examresults(examresults)

    total = len(examresults)
    print(f"marks for {total-len(missing)} participants merged ({total} participants total)",
          file=sys.stderr)
    if missing:
        print("missing marks:", missing, file=sys.stderr)
