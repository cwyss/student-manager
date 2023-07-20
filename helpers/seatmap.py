#!/usr/bin/env python3

import sys


steps = []
for a in sys.argv[1:]:
    steps.append(int(a))

if len(steps)==3:
    len_room = steps[2]
    len_row = steps[1]
    skip = steps[0]

    len_room += 1
    
    seats = []
    i = 1
    while i<len_room:
        next_row = min(i+len_row, len_room)
        while i<next_row:
            seats.append(i)
            i += skip
        i = next_row+len_row

    print("%d seats total\n" % len(seats))
    print(seats)
    
else:
    print("USAGE: seatmap.py stepsizes")
    sys.exit(1)

