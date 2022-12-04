#!/usr/bin/python3

import os
import re
import sys
import time
import threading

import numpy as np
import PySimpleGUI as sg


def readgen(fname):
    with open(fname, 'r') as f:
        for line in f.readlines():
            yield line
            
def console_timer(msg, expiry_time, window):
    """
    A worker thread that communicates with the GUI through a queue
    This thread can block for as long as it wants and the GUI will not be affected
    :param seconds: (int) How long to sleep, the ultimate blocking call
    :param gui_queue: (queue.Queue) Queue to communicate back to GUI that task is completed
    :return:
    """
    window['-CONSOLE-'].update(msg)
    time.sleep(expiry_time) # sleep for a while
    window['-CONSOLE-'].update(' ')  # put a message into queue for GUI

def process_csv_files(input_files, output_dir, labels):
    
    os.chdir(output_dir)

    for fname in input_files.split(';'):
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
                
        fname = os.path.basename(fname)
        fname = os.path.splitext(fname)[0] + '_processed.csv'
        fname = os.path.join(output_dir, fname)
        
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
input_files = [
    [
        sg.Text('Input file(s)'), 
        sg.In(size=(25, 1), 
        enable_events=True,
        key='-INPUT-'), 
        sg.FilesBrowse(file_types=[(EXTENSION, f"*.{EXTENSION}")])
    ]
]
output_dir = [
    [
        sg.Text('Output directory'),
        sg.In(size=(25, 1),
        enable_events=True,
        key='-OUTPUTDIR-'),
        sg.FolderBrowse()
    ]
]
layout = [
    [sg.Column(input_files)],
    [sg.Column(output_dir)],
    [sg.Text('Enter values for:')],
    [sg.Text('Channel 0'), sg.InputText()],
    [sg.Text('Channel 1'), sg.InputText()],
    [sg.Text('Channel 2'), sg.InputText()],
    [sg.Text('Channel 0, Channel 1'), sg.InputText()],
    [sg.Text('Channel 0, Channel 2'), sg.InputText()],
    [sg.Text('Channel 1, Channel 2'), sg.InputText()],
    [sg.Text('Channel 0, Channel 1, Channel 2'), sg.InputText()],
    [sg.Text("", size=(0, 1), key='-CONSOLE-')],
    [sg.Button('OK'), sg.Button('Cancel')]
]

if __name__ == '__main__':
    # Create the Window
    window = sg.Window("CODI CSV Processor", layout)
    input_key_list = [key for key, value in window.key_dict.items() if isinstance(value, sg.Input)]
    exe_time = time.time()
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        window.refresh()
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if event == '-INPUT-':
            input_files = values['-INPUT-']
        if event == '-OUTPUTDIR-':
            output_dir = values['-OUTPUTDIR-']
        if event == "OK":
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
                threading.Thread(target=process_csv_files, args=(input_files, output_dir, labels), daemon=True).start()
                msg, expiry_time = f'Done! Your processed files are in the output directory.', 7
            else:
                msg, expiry_time = 'Please check input values!', 2
            threading.Thread(target=console_timer, args=(msg, expiry_time, window), daemon=True).start()

    window.close()
    sys.exit()