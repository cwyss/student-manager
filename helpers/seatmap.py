#!/usr/bin/env python3

import sys


class ArgumentError(Exception):
    pass


class SeatMapper:
    def __init__(self, args):
        if len(args)==0:
            raise ArgumentError
        try:
            self.step = int(args[0])
            self.blockparams = []
            for block in args[1:]:
                self.blockparams.append(self.decode_blockparams(block))
            # for a in args[1:]:
            #     t = a.partition(':')
            #     if t[1]!=':':
            #         raise ArgumentError
            #     i = int(t[0]) - 1
            #     t = t[2].partition(':')
            #     n = int(t[0])
            #     if t[1]==':':
            #         t = t[2].partition(':')
            #         rowlength = int(t[0])
            #         if t[1]==':':
            #             rowshift = int(t[2])
            #         else:
            #             rowshift = 0
            #     else:
            #         rowlength = n - i
            #         delta = 0
            #     self.blockparams.append((i,n,rowlength,rowshift))
        except ValueError:
            raise ArgumentError

    def decode_blockparams(self, block):
        fields = block.split(':')
        if len(fields)<2 or len(fields)>5:
            raise ArgumentError
        i = int(fields[0]) - 1
        n = int(fields[1])
        if len(fields)>=3:
            rowlength = int(fields[2])
        elif len(fields)==2:
            rowlength = n - i
            rowshift = i
        if len(fields)>=4:
            rowshift = int(fields[3])
        elif len(fields)==3:
            rowshift = 0
        if len(fields)>=5:
            rowincr = int(fields[4])
        else:
            rowincr = 0
        return (i,n,rowlength,rowshift,rowincr)

    def generate(self):
        seats = []
        for block in self.blockparams:
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
        firstseat,n,rowlength,rowshift,rowincr = blockdata
        startrow = (firstseat-rowshift) // rowlength
        rowoffset = startrow*rowlength + rowshift
        seatoffset = firstseat-rowoffset
        seats = []
        while rowoffset<n:
            newseats = list(range(1+rowoffset+seatoffset,
                                  min(n,rowoffset+rowlength) + 1,
                                  self.step))
            seats.extend(newseats)
            rowoffset += 2*rowlength + rowincr
            rowlength += 2*rowincr
        return seats

try:
    mapper = SeatMapper(sys.argv[1:])
    seats = mapper.generate()

    if seats:
        print("%d seats total\n" % len(seats))
        print(seats)

except ArgumentError:
    print("""USAGE: seatmap.py step blocks...

step: seat increment

block: i:n[:k[:s[:d]]]
   first seat i, last possible seat n, row length k,
   row shift s, row length increment d"""
          )
    sys.exit(1)

