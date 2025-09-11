#!/usr/bin/env python3

import csv, sys, re


def read_slregist_csv(fname):
    csvfile = open(fname, newline='')
    reader = csv.reader(csvfile, delimiter=';')
    regist = {}
    matrikel = None
    for row in reader:
        if len(row)==4:
            matrikel_field = row[1].split('@')[0]
            if matrikel_field.isdigit():
                matrikel = int(matrikel_field)
                entry = {'matrikel': matrikel,
                         'name': row[0],
                         'status': row[2],
                         'subject_long': [row[3]]}
                if entry['status']=='storniert':
                    matrikel = None
                    continue
                if matrikel in regist:
                    raise Exception("duplicate matrikel number", matrikel)
                regist[matrikel] = entry
        elif len(row)==1 and matrikel:
            regist[matrikel]['subject_long'].append(row[0])
    return regist


def separate_first_name(regist):
    for entry in regist.values():
        parts = entry['name'].split(',')
        entry['name'] = parts[0].strip()
        entry['first_name'] = parts[1].strip()


def find_resit_fields(row):
    try:
        matrikel_field = row.index('Matrikelnummer')
        resit_field = row.index('Versuch (V)')
        return {
            'matrikel': matrikel_field,
            'resit': resit_field
        }
    except ValueError:
        raise Exception("resit file: Column names not recognised") from None

def read_resit_file(fname):
    csvfile = open(fname, newline='')
    reader = csv.reader(csvfile, delimiter=';')

    fields = None
    try:
        while not fields:
            row = next(reader)
            if row[0]=='startHISsheet':
                row = next(reader)
                fields = find_resit_fields(row)
    except (StopIteration, IndexError):
        raise Exception("resit file: HIS csv table not found") from None

    resits = []
    for row in reader:
        if row[0]=='endHISsheet':
            break
        resits.append([int(row[fields['matrikel']]),
                       int(row[fields['resit']])])
    return resits

def add_resits(regist_dict, resit_file):
    resits = read_resit_file(resit_file)
    for (matrikel,resit_count) in resits:
        if matrikel in regist_dict:
            regist_dict[matrikel]['resit'] = resit_count


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
    'Wirtschaftsingenieurwesen Elektrotechnik': 'WIng',
    'Smart and Sustainable Systems': 'SSS',
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
subject_translate_master = {
    'Elektrotechnik': 'ET',
    'Electrical Engineering': 'ET',
    'Informationstechnologie': 'IT'
}

def parse_subject(subject_lines, parse_for_master):
    if not parse_for_master:
        regexpr = r"Bachelor ([\w\(][\w \(\).]*).*?\((\d+)\. Fachsem"
    else:
        regexpr = r"Master ([\w\(][\w \(\).]*).*?\((\d+)\. Fachsem"
    result = []
    for line in subject_lines:
        match = re.match(regexpr, line)
        if match:
            raw_subj = match.group(1).strip()
            try:
                subject = subject_translate[raw_subj]
                result.append((subject, int(match.group(2)), parse_for_master))
            except KeyError:
                pass
    return result

def get_current_subject(subject_entries, parse_for_master):
    current = None
    for se in subject_entries:
        if not current or se[1] < current[1]:
            current = se
    if current:
        if not parse_for_master or current[2] == True:
            return current[0:2]
        else:
            return ("Ba "+current[0], current[1])
    else:
        return None

Unknown_subjects = {}

def process_subjects(regist, parse_for_master):
    for entry in regist.values():
        long_subject = entry['subject_long']
        subject_entries = parse_subject(long_subject, parse_for_master=False)
        if parse_for_master:
            subject_entries.extend(
                parse_subject(long_subject, parse_for_master=True)
                )
        current = get_current_subject(subject_entries, parse_for_master)
        if current:
            (subj,sem) = current
            entry['subject'] = subj
            entry['semester'] = sem
        elif DEBUG:
            Unknown_subjects[entry['matrikel']] = entry['subject_long']


def separate_by_subject(regist):
    regist_by_subject = {}
    for reg in regist.values():
        try:
            subj = reg['subject']
        except KeyError:
            subj = 'unknown'
        if subj in regist_by_subject:
            regist_by_subject[subj].append(reg)
        else:
            regist_by_subject[subj] = [reg]
    return regist_by_subject


def prepare_exam_data(examfile_list, resit_file, parse_for_master):
    regist = {}
    for sl_exam_file in examfile_list:
        regist |= read_slregist_csv(sl_exam_file)

    separate_first_name(regist)
    # translate_status(regist)
    if resit_file:
        add_resits(regist, resit_file)

    process_subjects(regist, parse_for_master)
    regist_by_subject = separate_by_subject(regist)
    return regist_by_subject


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
            line = ';'.join(data)
            if 'resit' in reg:
                line += f";{reg['resit']}"
            print(line)


def print_unknown_subjects():
    matrikel = list(Unknown_subjects)
    matrikel.sort()
    for m in matrikel:
        print("unknown subj %d: %s\n" % (m, Unknown_subjects[m]),
              file=sys.stderr)



DEBUG = False
HELP = False
IS_MASTER = False
files = []
resit_file = None

special = None
for arg in sys.argv[1:]:
    if special=='resit_file':
        resit_file = arg
        special = None
    else:
        if arg=='-D':
            DEBUG = True
        elif arg=='-h':
            HELP = True
        elif arg=='-m':
            IS_MASTER = True
        elif arg=='-r':
            special = 'resit_file'
        else:
            files.append(arg)

if not files:
    print(
        """Usage: slexam-importer.py [OPTION] REGISTRATION_FILES
Convert studilöwe exam registrations to student manager exam import file

REGISTRATION_FILES: csv files with registrations.
             Excel exports from studilöwe ("Teilnehmerliste"), converted to
             csv, with fields "Name", "E-Mail", "Status", "Studiengänge",
             separator ';'

Options
  -m       registrations for "master" course, prepare subjects accordingly
  -D       debug mode: write unrecognised subjects to stderr
  -r file  read resit count from csv file containing fields "Matrikelnummer"
           and "Versuch (V)" (studilöwe export of "Notenliste")
  -h       display this help"""
    )
    sys.exit(2)

regist_by_subj = prepare_exam_data(files, resit_file, parse_for_master=IS_MASTER)
print_exam_data(regist_by_subj)
if DEBUG:
    print_unknown_subjects()

