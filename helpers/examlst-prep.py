#!/usr/bin/env python3

import csv, sys, re

FIELDS = {
    'name': 1,
    'firstname': 2,
    'matrikel': 3,
    'resit': 4,
    'subject': 8
}


def read_examlst_csv(fname):
    csvfile = open(fname, newline='')
    reader = csv.reader(csvfile, delimiter=';')
    regist = []
    for row in reader:
        if row[0].isdecimal():
            regist.append({'matrikel': row[FIELDS['matrikel']],
                           'name': row[FIELDS['name']],
                           'firstname': row[FIELDS['firstname']],
                           'resit': row[FIELDS['resit']],
                           'subject_long': row[FIELDS['subject']]
                           })
    return regist

subjects_BA = [
    ("Angewandte Naturwissenschaften", "AS"),
    ("Elektrotechnik", "ET"),
    ("Wirtschaftsingenieurwesen Elektrotechnik", "WIng"),
    ("Informationstechnologie und Medientechnologie", "IT"),
    ("Informatik", "Info")
]
subjects_Kombi = [
    ("Physik", "Kombi Phy"),
    ("Informatik", "Kombi Inf")
]

def prepare_subjects(master):
    transl = {}
    if not master:
        for subj, short in subjects_BA:
            key = "Studiengang " + subj \
                + " mit dem Abschluss Bachelor of Science"
            transl[key] = short
        for subj, short in subjects_Kombi:
            key1 = "Teilstudiengang " + subj \
                + " im Kombinatorischen Studiengang mit dem Abschluss Bachelor of Arts"
            key2 = "Teilstudiengang  " + subj \
                + " zur Erweiterung des Kombinatorischen Studienganges mit dem Abschluss Bachelor of Arts"
            transl[key1] = short
            transl[key2] = short
    return transl

def translate_subjects(regist, master=False):
    transl = prepare_subjects(master)
    # for s in transl:
    #     print(s, transl[s], file=sys.stderr)
    unknown = []
    for e in regist:
        try:
            e['subject'] = transl[e['subject_long']]
        except KeyError:
            unknown.append(e)
    return unknown

def sort_subjects(regist):
    d = {}
    for e in regist:
        subj = e.get('subject')
        if subj in d:
            d[subj].append(e)
        elif subj:
            d[subj] = [e]
    return d


def prepare_exam_data(files, parse_for_master=False):
    regist = []
    for f in files:
        regist.extend(read_examlst_csv(f))
    unknown = translate_subjects(regist, parse_for_master)
    rdict = sort_subjects(regist)
    return rdict, unknown


def print_exam_data(rdict):
    for subj in rdict:
        print("subject: " + subj + "\n")
        for i,e in enumerate(rdict[subj]):
            line = [
                str(i+1),
                e['name'],
                e['firstname'],
                e['matrikel'],
                e['resit']
            ]
            print(';'.join(line))
        print()
    
def print_unknown_subjects(unkown):
    if len(unknown)>0:
        d = {}
        for e in unknown:
            subj = e['subject_long']
            if subj in d:
                d[subj].append(e)
            else:
                d[subj] = [e]

        print("*unknown subjects*\n", file=sys.stderr)
        for subj in d:
            line = [e['name'] + '(' + e['matrikel'] + ')'
                    for e in d[subj]]
            print(subj + ": " + ", ".join(line), file=sys.stderr)



QUIET = False
HELP = False
IS_MASTER = False
files = []

for arg in sys.argv[1:]:
    if arg=='-q':
        QUIET = True
    elif arg=='-h':
        HELP = True
    elif arg=='-m':
        IS_MASTER = True
    else:
        files.append(arg)

if HELP or not files:
    print(
        """Usage: examlst-prep.py [OPTIONS] REGISTRATION_FILES
Prepare exam registration lists for import in student manager:
translate subjects and group by them.

REGISTRATION_FILES: csv files with registrations.
             fields: name, first name, matrikel, resit, subject
             in columns 2,3,4,5,9, separator ';'

Options
  -m      registrations for "master" course, prepare subjects accordingly
  -q      quiet mode: do not write unrecognised subjects to stderr
  -h      display this help""",
        file=sys.stderr
    )
    sys.exit(2)

rdict, unknown = prepare_exam_data(files, parse_for_master=IS_MASTER)
print_exam_data(rdict)
if not QUIET:
    print_unknown_subjects(unknown)
