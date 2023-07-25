#!/usr/bin/env python3

import sys


class ArgumentError(Exception):
    pass


class stepsizes:
    def __init__(self, args):
        if len(args)==0:
            raise ArgumentError
        try:
            self.skip = int(args[0])
            self.steps = []
            for a in args[1:]:
                t = a.partition(':')
                if t[1]!=':':
                    raise ArgumentError
                i = int(t[0])
                t = t[2].partition(':')
                n = int(t[0]) + 1
                if t[1]==':':
                    t = t[2].partition(':')
                    rowlength = int(t[0])
                    if t[1]==':':
                        delta = int(t[2])
                    else:
                        delta = 0
                else:
                    rowlength = n - i
                    delta = 0
                self.steps.append((i,n,rowlength,delta))
        except ValueError:
            raise ArgumentError

    def generate(self):
        seats = []
        for block in self.steps:
            seats.extend(self.gen_block(block))
        return seats
        
    def gen_simple(self):
        max_seat = stepsizes.len_room + 1
        seats = []
        i = 1 + self.shift
        while i<max_seat:
            next_row = min(i+self.len_row, max_seat)
            while i<next_row:
                seats.append(i)
                i += self.skip
            i = next_row + self.len_row
        return seats

    def gen_block(self, blockdata):
        i,n,k,d = blockdata
        seats = []
        while i<n:
            next_row = min(i+k,n)
            while i<next_row:
                seats.append(i)
                i += self.skip
            i = next_row + k + d
            k += 2*d
        return seats

try:
    stepsizes = stepsizes(sys.argv[1:])
    seats = stepsizes.generate()
    
    if seats:
        print("%d seats total\n" % len(seats))
        print(seats)

except ArgumentError:
    print("""USAGE: seatmap.py skip blocks...

block: i:n[:k[:d]]
   first seat i, last possible seat n, row length k,
   row length increment d"""
          )
    sys.exit(1)

