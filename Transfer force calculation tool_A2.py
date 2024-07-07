# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 22:02:51 2023

@author: namit
"""

import csv
import numpy as np
from class_definitions import beam_class, node_class
import tkinter as tk
import tkinter.filedialog
import os
import sys
from tabulate import tabulate
import functools
from multiprocessing import Pool, Manager
import time
# from calculate_tf import calculate_tf
from sys import getsizeof
from pympler import asizeof


def get_file_paths():
    #Opens a folder browser from which user can select the folder containing structure data files
    #Returns the file paths for files containing node, beam and force data
    
    #Code for dialog box taken from https://stackoverflow.com/questions/19944712/browse-for-file-path-in-python
    root = tkinter.Tk()
    root.withdraw() #use to hide tkinter window
    
    currdir = os.getcwd()
    tempdir = tk.filedialog.askdirectory(parent=root, initialdir=currdir, title='Please select a directory')
    
    for file in os.listdir(tempdir):
        if 'Nodes' in file:
            node_file_path = os.path.join(tempdir, file)
        elif 'Beams' in file:
            beam_file_path = os.path.join(tempdir, file)
        elif 'Forces' in file:
            force_file_path = os.path.join(tempdir, file)
    return node_file_path, beam_file_path, force_file_path



def read_node_data(file_path):
    #Reads node coordinate data from a text file at file path given by the user
    #Returns a dictionary mapping node numbers to corresponding node class objects
    with open(file_path, mode='r') as infile:
        reader = csv.reader(infile)
        node_data = {}
        for row in reader:
            if row and row[0][0].isnumeric():
                # print(row)
                row_list = row[0].split('\t')
                # Convert list to numpy array of type int
                row_list_int = np.array(row_list, dtype=int)
                node_data[row_list_int[0]] = node_class(row_list_int[1], row_list_int[2], row_list_int[3])
    return node_data

def read_beam_data(file_path, node_data):
    #Reads beam coordinate data from a text file at file path given by the user
    #Returns a dictionary mapping beam numbers to corresponding beam class objects
    with open(file_path, mode='r') as infile:
        reader = csv.reader(infile)
        beam_data = {}
        for row in reader:
            if row and row[0][0].isnumeric():
                # print(row)
                row_list = row[0].split('\t')
                # Convert list to numpy array of type int
                row_list_int = np.array(row_list, dtype=int)
                beam_num = row_list_int[0]
                nodeA = row_list_int[1]
                nodeB = row_list_int[2]
                #Add beam number to node attribute conn_beams
                node_data[nodeA].conn_beams.add(beam_num)
                node_data[nodeB].conn_beams.add(beam_num)
                #Add beam number to beam_data
                beam_data[beam_num] = beam_class(nodeA, nodeB, node_data)
    return beam_data

def read_force_data(file_path, beam_data):
    #Reads force data for all load cases from a text file and stores it in corresponding beam objects
    #Returns the force units
    with open(file_path, mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            if row:
                # print(row)
                row_list = row[0].split('\t')
                if row_list[0] == 'Force Unit:': force_unit = row_list[1]
                # print(row_list)
                if len(row_list) != 9 or not row_list[2].isnumeric(): continue
                # Convert list to numpy array of type int
                # row_list_int = np.array(row_list, dtype=float)    
                LC = int(row_list[2])
                # load_values = tuple(np.array(row_list[-6:], dtype = float))
                axial = float(row_list[3])
                if row_list[0].isnumeric(): beam = int(row_list[0])
                if row_list[1].isnumeric(): node =int(row_list[1])
                    
                if node == beam_data[beam].start:         
                    beam_data[beam].fx_s[LC] = axial
                else:
                    beam_data[beam].fx_e[LC] = axial
    return force_unit

def get_user_input(beam_data):
    #Gets beam number, node number and load case numbers from the user
    #Data validation on user input performed to ensure valid inputs
    #Returns validated user inputs
    count = 0
    while True:
        count += 1 
        if count == 4: sys.exit('Maximum attempts exceeded.')
        #Code for try catch taken from https://automatetheboringstuff.com/2e/chapter8/
        try:
            start_LC = int(input('Enter start load case number: '))
            if not start_LC in next(iter(beam_data.values())).fx_s:
                print('Start load case number not found.')
                continue
            end_LC = int(input('Enter end load case number: '))
            if not end_LC in next(iter(beam_data.values())).fx_s:
                print('End load case number not found.')
                continue
        except:
            print('Please enter numeric digits.')
            continue
        break
    return start_LC, end_LC

def calculate_tf(node_tf, connected_beams, start_LC, end_LC):
    LC_range = range(start_LC, end_LC)
    #Find beams connected to the node_tf
    # connected_beams = list(node_data[node_tf].conn_beams) 
    beam_list = [beam_num for beam_num in connected_beams if connected_beams[beam_num].is_beam()]
    
    beam_tf_list = []
    #If there are no orthogonal beams at this node than move on to the next node
    if not beam_list: return []
    connected_braces = []
    #For each beam in beam_list, calculate the transfer_force and store it in beam attribute
    for beam_tf in beam_list:
        #Find braces connected to the node specified by the user (at an angle less than 70 degrees w.r.t. the user-specified beam)    
        connected_braces = [beam_num for beam_num in connected_beams if connected_beams[beam_num].get_angle(connected_beams[beam_tf]) <= 70 and beam_num != beam_tf]
        
        if not connected_braces: continue
                              
        tf_max = 0
        #For each load case, calculate the transfer force and append to tf_LC
        for load_case in LC_range:
            #Skip load case if it is not present in the structure data file
            if not load_case in connected_beams[beam_tf].fx_s: continue
            #Check if the user-specified node is at beam start or beam end:
            if node_tf == connected_beams[beam_tf].start:
                tf = connected_beams[beam_tf].fx_s[load_case]
            else:
                tf = connected_beams[beam_tf].fx_e[load_case]
            # For each connected brace member, add component of axial force to transfer force
            for brace in connected_braces:
                cos_angle = np.cos(np.deg2rad(connected_beams[brace].get_angle(connected_beams[beam_tf])))
                if connected_beams[brace].shared_node(node_tf) == 0:
                    tf += (connected_beams[brace].fx_s[load_case]) * cos_angle
                else:
                    tf += (connected_beams[brace].fx_e[load_case]) * cos_angle
            if abs(tf) > tf_max:
                tf_max = round(abs(tf), 3)
                LC_max = load_case

        #Find maximum transfer force out of all the load cases
        if node_tf == connected_beams[beam_tf].start:
            # beam_data[beam_tf].tf_start = tf_max
            # beam_data[beam_tf].tf_LC_start = LC_max
            location = 'start'
        else:
            # beam_data[beam_tf].tf_end = tf_max
            # beam_data[beam_tf].tf_LC_end = LC_max
            location = 'end'
        beam_tf_list.append([beam_tf, location, tf_max, LC_max])
    return beam_tf_list


def main():
    #Get file paths from the user specified folder
    node_file_path, beam_file_path, force_file_path = get_file_paths()  
    #Get data from the text files in the user specified folder 
       
    node_data = read_node_data(node_file_path)
    # print(asizeof.asizeof(node_data)/10**6)
    beam_data = read_beam_data(beam_file_path, node_data)
    # print(asizeof.asizeof(beam_data)/10**6)
    force_unit = read_force_data(force_file_path, beam_data)
    
    # print(asizeof.asizeof(beam_data[1])/10**6)
    # print(asizeof.asizeof(node_data)/10**6)
    # quit
    
    # mgr = Manager()
    # mgr_nodes = mgr.dict(node_data)


    # mgr_beams = mgr.dict(beam_data)

    # print(mgr_nodes[1].conn_beams)
    # print(mgr_beams[1].fx_s)
    # quit
    #Get beam, node, start- and end- load case numbers from the user for transfer force calculation
    start_LC, end_LC = get_user_input(beam_data)
    
    #Create a list of loads cases based on the start and end load case numbers entered by the user
    # LC_range = range(start_LC, end_LC + 1)
    
    node_tf = list(node_data.keys())
    connected_beam_list = []
    for node in node_tf:
        connected_beam = {}
        for beam in node_data[node].conn_beams:
            connected_beam[beam] = beam_data[beam]
        connected_beam_list.append(connected_beam)
    ## partial_func = lambda x: calculate_tf(x, node_data, beam_data, LC_range)
    
    # Line below needs to be uncommented for sequential implementation
    partial_func = functools.partial(calculate_tf, start_LC= start_LC, end_LC =end_LC)
    start = time.time()
    #Sequential implementation (uncomment line below for sequential implementation)
    results = map(partial_func, node_tf, connected_beam_list)
    
    # Parallel impementation (comment out the next two lines for sequential implementation)
    # with Pool(1) as pool:
    #     # results = pool.map(partial_func, node_tf)
    #     results = pool.starmap(calculate_tf, [(node, connected_beam_list[i], start_LC, end_LC) for i, node in enumerate(node_tf)])
    end = time.time()
    print(end - start)
    start = time.time()
    for beam_results in results:
        if beam_results:
            for item in beam_results:
                beam_tf, location, tf_max, LC_max = item
                if location == 'start':
                    beam_data[beam_tf].tf_start = tf_max
                    beam_data[beam_tf].tf_LC_start = LC_max
                else:
                    beam_data[beam_tf].tf_end = tf_max
                    beam_data[beam_tf].tf_LC_end = LC_max
    
    end = time.time()
    print(end - start)
    
    table_header = [["Beam", f"Transfer Force Start ({force_unit})", "Load Case", f"Transfer Force End ({force_unit})", "Load Case"]]
    table_data = [[beam_num, beam_data[beam_num].tf_start, beam_data[beam_num].tf_LC_start,beam_data[beam_num].tf_end, beam_data[beam_num].tf_LC_end] 
                  for beam_num, _ in beam_data.items() if beam_data[beam_num].tf_LC_start or beam_data[beam_num].tf_LC_end]
    table = table_header + table_data
    
    #Print the transfer forces in a text file
    with open('output.txt', 'w') as f:
        f.write(tabulate(table, headers = 'firstrow', tablefmt='grid'))
    
if __name__=='__main__':
    main()
