#!/usr/bin/env python3

import csv,sys


def read_header(csvreader):
    first_line = next(csvreader)

    assert(first_line[2]=='ID-Nummer')
    assert(len(first_line)>=7)

    return (2,4,5,6)
    
def read_bewertungen(fname):
    filehandle = open(fname, newline='')
    csvreader = csv.reader(filehandle, delimiter=';')

    fields = read_header(csvreader)

    for line in csvreader:
        if line[fields[0]].isdigit():
            matrikel = line[fields[0]]

            anyresult = False
            badresult = False
            for tst_index in fields[1:]:
                points = line[tst_index]
                if points!='-':
                    anyresult = True
                    if float(points)<=0.0:
                        badresult = True
                elif anyresult:
                    badresult = True
            if not anyresult:
                bestanden = '-'
            elif badresult:
                bestanden = 'fail'
            else:
                bestanden = 'pass'

            print(matrikel + ';' + bestanden)

    
if len(sys.argv)!=2:
    print("""Usage: wtest-importer.py FILE
convert moodle test data from FILE (csv) for import into studmgr"""
          )
else:
    bew_fname = sys.argv[1]
    read_bewertungen(bew_fname)
