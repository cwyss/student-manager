#!/usr/bin/env python3

import csv, sys, re


def read_slregist_csv(fname):
    csvfile = open(fname, newline='')
    reader = csv.reader(csvfile, delimiter=';')
    regist = []
    for row in reader:
        if len(row)==4:
            matrikel_field = row[1].split('@')[0]
            if matrikel_field.isdigit():
                regist.append({'matrikel': int(matrikel_field),
                               'name': row[0],
                               # 'status': row[2],
                               'subject_long': [row[3]]
                })
        elif len(row)==1 and len(regist)>0:
            regist[-1]['subject_long'].append(row[0])
    return regist


def separate_first_name(regist):
    for e in regist:
        parts = e['name'].split(',')
        e['name'] = parts[0].strip()
        e['first_name'] = parts[1].strip()

# def translate_status(regist):
#     status_dict = {
#         'angemeldet': 'AN',
#         'zugelassen': 'ZU',
#         'niedrige Priorität': 'NP',
#         'abgelehnt niedrige Priorität': 'NP',
#         'hohe Priorität': 'HP',
#         'abgelehnt hohe Priorität': 'HP',
#         'storniert': 'ST',
#         'abgelehnt': 'ST'
#     }
#     for e in regist:
#         e['status'] = status_dict[e['status']]


subject_translate = {
    'Elektrotechnik': 'ET',
    'Electrical Engineering': 'ET',
    'Informationstechnologie': 'IT',
    'Informatik': 'Info',
    'Wirtschaftsing. Elektrotechnik': 'WIng',
    'applied science (Kombi) Physik': 'AS',
    'applied science (Kombi) Chemie': 'AS',
    'applied science (Kombi) Informatik': 'AS',
    'Angewandte Naturwissenschaften': 'AS',
    '(Kombi) Informatik': 'Kombi Inf',
    '(Erweiterung) Informatik': 'Kombi Inf',
    '(Kombi) Physik': 'Kombi Phy',
    '(Erweiterung) Physik': 'Kombi Phy',
    '(Kombi) Elektrotechnik': 'Kombi ET',
    'of Education Sonderpäd (Kombi) Mathematik': 'SoPäd Mat'
}

def parse_subject(subject_lines):
    result = []
    for line in subject_lines:
        match = re.match(r"Bachelor ([\w\(][\w \(\).]*).*?\((\d+)\. Fachsem",
                         line)
        if match:
            raw_subj = match.group(1).strip()
            try:
                subject = subject_translate[raw_subj]
                result.append((subject, int(match.group(2))))
            except KeyError:
                pass
    return result

def get_current_subject(subject_entries):
    if subject_entries:
        current = 0
        for (i,se) in enumerate(subject_entries):
            if i==0:
                pass
            elif subject_entries[current][1] > se[1]:
                current = i 
        return subject_entries[current]
    else:
        return None

Unknown_subjects = {}

def process_subjects(regist):
    for e in regist:
        current = get_current_subject(parse_subject(e['subject_long']))
        if current:
            (subj,sem) = current
            e['subject'] = subj
            e['semester'] = sem
        elif DEBUG:
            Unknown_subjects[e['matrikel']] = e['subject_long']


def separate_by_subject(regist_lst):
    regist_dict = {}
    for reg in regist_lst:
        try:
            subj = reg['subject']
        except KeyError:
            subj = 'unknown'
        if subj in regist_dict:
            regist_dict[subj].append(reg)
        else:
            regist_dict[subj] = [reg]
    return regist_dict


def prepare_exam_data(examfile_list):
    regist = []
    for sl_exam_file in examfile_list:
        regist.extend(read_slregist_csv(sl_exam_file))
    separate_first_name(regist)
    # translate_status(regist)
    process_subjects(regist)
    regist_dict = separate_by_subject(regist)
    return regist_dict


def print_exam_data(regist_dict):
    subjects = list(regist_dict)
    subjects.sort()
    for (n,subj) in enumerate(subjects):
        if n>=1:
            print()
        print("subject:", subj, "\n")
        regist_dict[subj].sort(
            key = lambda reg: reg['name']+reg['first_name']
        )
        for (i,reg) in enumerate(regist_dict[subj]):
            data = (
                str(i+1),
                reg['name'], reg['first_name'],
                str(reg['matrikel'])
            )
            print(';'.join(data))


def print_unknown_subjects():
    matrikel = list(Unknown_subjects)
    matrikel.sort()
    for m in matrikel:
        print("unknown subj %d: %s\n" % (m, Unknown_subjects[m]),
              file=sys.stderr)



DEBUG = False
HELP = False
files = []

for arg in sys.argv[1:]:
    if arg=='-D':
        DEBUG = True
    elif arg=='-h':
        HELP = True
    else:
        files.append(arg)

if not files:
    print(
        """Usage: slexam-importer.py [OPTION] REGISTRATION_FILES
Convert studilöwe exam registrations to student manager exam import file

REGISTRATION_FILES: csv files with studilöwe registrations. 
             Excel exports converted to csv, with fields: "Name", 
             "E-Mail", "Status", "Studiengänge", separator ';'

Options
  -D      debug mode: write unrecognised subjects to stderr
  -h      display this help"""
    )
    sys.exit(2)

regist_dict = prepare_exam_data(files)
print_exam_data(regist_dict)
if DEBUG:
    print_unknown_subjects()

