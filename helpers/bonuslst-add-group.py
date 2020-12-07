#!/usr/bin/env python3

import csv
import sys

def read_group_dict(grouplst):
    csvfile = open(grouplst,newline='')
    cr = csv.reader(csvfile,delimiter=';')
    gdict = {}
    for row in cr:
        if row[0].isdigit() and row[1].isdigit():
            gdict[int(row[0])] = int(row[1])
    return gdict

def read_bonuslst(bonuslst):
    csvfile = open(bonuslst,newline='')
    cr = csv.reader(csvfile,delimiter=';')
    bonustable = []
    for row in cr:
        if row[0].isdigit():
            row[0] = int(row[0])
            bonustable.append(row)
    return bonustable

def print_bonuslst(bonus_table,group_dict):
    bonuslst = []
    for bentry in bonus_table:
        matrikel = bentry[0]
        try:
            group = group_dict[matrikel]
            line = "%d;%d" % (matrikel,group)
            if len(bentry)>1:
                line += ';' + ';'.join(bentry[1:])
            bonuslst.append(line)
        except KeyError:
            if sum([len(x) for x in bentry[1:]])>0:
                print("no grp: ", bentry, file=sys.stderr)
            pass
    return bonuslst


        
if len(sys.argv)<3:
    print("USAGE %s bonuslst.csv grouplst.csv" % sys.argv[0])
    sys.exit()
bonuslst = sys.argv[1]
grouplst = sys.argv[2]

group_dict = read_group_dict(grouplst)
bonus_table = read_bonuslst(bonuslst)
bonuslst = print_bonuslst(bonus_table,group_dict)
print("matrikel;gruppe;eintraege...")
for line in bonuslst:
    print(line)
