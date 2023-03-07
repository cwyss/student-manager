#!/usr/bin/env python3

import sys,math

def calc_stepsize(minpoints, maxpoints):
    span = maxpoints-minpoints+0.5
    stepsize = math.ceil(span/5)/2

    #extspan = math.ceil(span/stepsize)*stepsize
    extspan = stepsize*10
    smallsteps = int((extspan-span)//0.5)

    check = (stepsize-0.5)*smallsteps + stepsize*(10-smallsteps)
    print("point span:", span)
    print("large step:", stepsize)
    print("small steps:", smallsteps)

    return (stepsize,smallsteps)

PACKET_PATTERN = {
    1: (10,),
    2: (5,5),
    3: (3,3,4),
    4: (2,3,2,3),
    5: (2,2,2,2,2),
    6: (3,2,3,2),
    7: (4,3,3),
    8: (5,5),
    9: (10,)
}
def gen_spacing_pattern(smallsteps, shift):
    if smallsteps==0:
        spacing = 10*[0]
    else:
        pattern = PACKET_PATTERN[smallsteps]
        shift = min(shift, pattern[0]-1, pattern[-1]-1)
        spacing = []
        for n in pattern:
            if smallsteps<=5:
                ext = n*[0]
                ext[shift] = 1
            else:
                ext = n*[1]
                ext[-shift-1] = 0
            spacing.extend(ext)
    print("spacing pattern (1 for small step):", spacing)
    return spacing

MARKS = ['1.0','1.3','1.7','2.0','2.3','2.7','3.0',
         '3.3','3.7','4.0']
def print_spacing(minpoints, stepsize, spacing):
    lower_points = 10*[minpoints]
    for (i,small) in enumerate(spacing[0:9]):
        points = lower_points[i] + stepsize
        if small==1:
            points -= 0.5
        lower_points[i+1] = points
    for i in range(10):
        print("%s: %4.1f  (%d)" % (MARKS[i],lower_points[-1-i],spacing[-1-i]))

    
if len(sys.argv)>=3 and len(sys.argv)<=4:
    Minpoints = float(sys.argv[1])
    Maxpoints = float(sys.argv[2])
    if len(sys.argv)==4:
        Shift = abs(int(sys.argv[3]))
    else:
        Shift = 0
else:
    print("""UASGE: genpoints.py MINPOINTS MAXPOINTS [SKIP]""")
    sys.exit(1)

(Stepsize, Smallsteps) = calc_stepsize(Minpoints, Maxpoints)
Spacing = gen_spacing_pattern(Smallsteps, Shift)
print_spacing(Minpoints, Stepsize, Spacing)
