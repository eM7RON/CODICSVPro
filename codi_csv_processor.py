import glob
import os
import re
import sys
import time

import numpy as np
import PySimpleGUI as sg


def readgen(fname):
    with open(fname, 'r') as f:
        for line in f.readlines():
            yield line

def process_csv_files(input_dir, output_dir, labels):
    os.chdir(input_dir)
    files = glob.glob('*.{}'.format(EXTENSION))
    for fname in files:
        os.chdir(input_dir)
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
                    if '[' in line:
                        line = ''.join([line.split('[')[0], ',' * (5 - length), '\n'])
                    else:
                        line = ''.join([line[:-1], ',' * (5 - length), '\n'])
                csv.append(line)
        os.chdir(output_dir)
        fname = fname[:-4] + '_processed.csv'
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

        df, new_df = new_df, [labels]

        for row in df:
            row = np.hstack(row)
            new_df.append(row)

        df = np.array(new_df).T

        np.savetxt(fname, df, delimiter=",", fmt='%s')

PATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
EXTENSION = 'csv'

sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
input_dir = [[sg.Text('Input directory'), sg.In(size=(25, 1), enable_events=True, key='INPUTDIR'), sg.FolderBrowse()]]
output_dir = [[sg.Text('Output directory'), sg.In(size=(25, 1), enable_events=True, key='OUTPUTDIR'), sg.FolderBrowse()]]
layout = [
    [sg.Column(input_dir)],
    [sg.Column(output_dir)],
    [sg.Text('Enter values for:')],
    [sg.Text('Channel 0'), sg.InputText()],
    [sg.Text('Channel 1'), sg.InputText()],
    [sg.Text('Channel 2'), sg.InputText()],
    [sg.Text('Channel 0, Channel 1'), sg.InputText()],
    [sg.Text('Channel 0, Channel 2'), sg.InputText()],
    [sg.Text('Channel 1, Channel 2'), sg.InputText()],
    [sg.Text('Channel 0, Channel 1, Channel 2'), sg.InputText()],
    [sg.Text("", size=(0, 1), key='CONSOLE')],
    [sg.Button('OK'), sg.Button('Cancel')]
]

if __name__ == '__main__':
    # Create the Window
    window = sg.Window("CODI CSV Processor", layout)
    input_key_list = [key for key, value in window.key_dict.items() if isinstance(value, sg.Input)]
    exe_time = time.time()
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        elif event == 'INPUTDIR':
            input_dir = values['INPUTDIR']
        elif event == 'OUTPUTDIR':
            output_dir = values['OUTPUTDIR']
        elif event == "OK":
            if all(map(str.strip, [values[key] for key in input_key_list])):
                labels = np.array(
                    [
                        " ",
                        values[0], 
                        values[1],
                        values[2],
                        values[3],
                        values[4],
                        values[5],
                        values[6],
                        "Total Positive"
                    ]
                )
                process_csv_files(input_dir, output_dir, labels)
                window['CONSOLE'].update(value='Done!')
                exe_time = time.time()
            else:
                window['CONSOLE'].update(value='Please check input values')
                exe_time = time.time()
        elif time.time() > exe_time + 5:
            window['CONSOLE'].update(value=' ')
        window.refresh()

    window.close()