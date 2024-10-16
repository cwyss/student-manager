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
                               'status': row[2],
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

def translate_status(regist):
    status_dict = {
        'angemeldet': 'AN',
        'zugelassen': 'ZU',
        'niedrige Priorität': 'NP',
        'abgelehnt niedrige Priorität': 'NP',
        'hohe Priorität': 'HP',
        'abgelehnt hohe Priorität': 'HP',
        'storniert': 'ST',
        'abgelehnt': 'ST'
    }
    for e in regist:
        e['status'] = status_dict[e['status']]


def parse_subject(subject_lines):
    subject_translate = {
        'Elektrotechnik': 'ET',
        'Electrical Engineering': 'ET',
        'Informationstechnologie': 'IT',
        'Informatik': 'Info',
        'Wirtschaftsing. Elektrotechnik': 'WIng',
        'Wirtschaftsingenieurwesen Elektrotechnik': 'WIng',
        'applied science (Kombi) Physik': 'AS',
        'applied science (Kombi) Chemie': 'AS',
        'applied science (Kombi) Informatik': 'AS',
        'Angewandte Naturwissenschaften': 'AS',
        '(Kombi) Informatik': 'Kombi Inf',
        '(Erweiterung) Informatik': 'Kombi Inf',
        '(Kombi) Physik': 'Kombi Phy',
        '(Erweiterung) Physik': 'Kombi Phy',
        '(Kombi) Elektrotechnik': 'Kombi ET',
        'of Education Sonderpäd (Kombi) Mathematik': 'SoPäd Mat',
        'Sonderpädagogik (Kombi) Mathematik': 'SoPäd Mat',
        'Smart and Sustainable Systems': 'SSS'
    }
    result = []
    for line in subject_lines:
        match = re.match(r"(?:Bachelor|B\.Ed\.) ([\w\(][\w \(\).]*).*?\((\d+)\. Fachsem",
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
            
def set_group(regist, group):
    for e in regist:
        e['group'] = str(group)


def prepare_registration_data(sl_group_files):
    regist = []
    for (i,groupfile) in enumerate(sl_group_files):
        grp_regist = read_slregist_csv(groupfile)
        separate_first_name(grp_regist)
        translate_status(grp_regist)
        process_subjects(grp_regist)
        set_group(grp_regist, i+1)

        regist.extend(grp_regist)
    return regist
        
def print_registration_data(regist):
    for e in regist:
        data = (
            str(e['matrikel']),
            e['name'], e['first_name'],
            '',
            e.get('subject',''),
            '',
            str(e.get('semester','')),
            e['status'],
            '',
            e['group']
        )
        print(';'.join(data))

def print_unknown_subjects():
    matrikel = list(Unknown_subjects)
    matrikel.sort()
    for m in matrikel:
        print("unknown subj %d: %s\n" % (m, Unknown_subjects[m]),
              file=sys.stderr)



DEBUG = False
group_filenames = None

if len(sys.argv)>=2:
    if sys.argv[1]=='-D':
        DEBUG = True
        group_filenames = sys.argv[2:]
    else:
        group_filenames = sys.argv[1:]

if not group_filenames:
    print("""Usage: slregist-importer.py [OPTION] gruppe1.csv ... gruppeN.csv
Convert studilöwe Belegungen to student manager registration file

gruppe?.csv: csv export of studilöwe excel file of one parallel group.
             fields: "Name", "E-Mail", "Status", "Studiengänge"
             separator: ';'

Options
  -D      debug mode: write unrecognised subjects to stderr""")
else:
    regist = prepare_registration_data(group_filenames)
    print_registration_data(regist)
    if DEBUG:
        print_unknown_subjects()

