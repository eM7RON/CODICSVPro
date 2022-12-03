import glob
import os
import re
import sys

import numpy as np


def readgen(fname):
    with open(fname, 'r') as f:
        for line in f.readlines():
            yield line


PATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')

path = sys.argv[1]
extension = 'csv'
os.chdir(path)
files = glob.glob('*.{}'.format(extension))

for fname in files:
    gen = readgen(fname)
    csv = []

    while True:
        try:
            line = gen.__next__()
        except StopIteration:
            break
        else:
            line = line.replace(', ', '//')
            length = len(PATTERN.split(line)[1::2])
            if length < 5:
                line = line[:-1] + (',' * (5 - length)) + '\n'
            csv.append(line)
    fname = fname[:-4] + '_reformatted.csv'
    with open(fname, 'w') as f:
        f.write(''.join(csv))


    df = np.genfromtxt(
        fname,
        delimiter=',',
        dtype=str,
        usecols=np.arange(0,5)
    )

    new_df = []

    for i in range(len(df)):
        if df[i, 0].startswith('Summary'):
            new_df.append([df[i, 0][20:], df[i + 9: i + 17, 2]])

    labels = np.array(
        [   
            " ",
            "CD63-568",
            "CD81-647",
            "CD9-488",
            '"CD63-568, CD81-647"',
            '"CD63-568, CD9-488"',
            '"CD81-647, CD9-488"',
            '"CD63-568, CD81-647, CD9-488"',
            "Total Positive"
        ]
    )

    df, new_df = new_df, [labels]

    for row in df:
        row = np.hstack(row)
        new_df.append(row)

    df = np.array(new_df).T

    np.savetxt(fname, df, delimiter=",", fmt='%s')