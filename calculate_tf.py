# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 01:53:26 2023

@author: namit
"""
import numpy as np

def calculate_tf(node_tf, node_data, beam_data, LC_range):
    
    #Find beams connected to the node_tf
    connected_beams = list(node_data[node_tf].conn_beams) 
    beam_list = [beam_num for beam_num in connected_beams if beam_data[beam_num].is_beam()]
    
    beam_tf_list = []
    #If there are no orthogonal beams at this node than move on to the next node
    if not beam_list: return []
    connected_braces = []
    #For each beam in beam_list, calculate the transfer_force and store it in beam attribute
    for beam_tf in beam_list:
        #Find braces connected to the node specified by the user (at an angle less than 70 degrees w.r.t. the user-specified beam)    
        connected_braces = [beam_num for beam_num in connected_beams if beam_data[beam_num].get_angle(beam_tf, beam_data) <= 70 and beam_num != beam_tf]
        
        if not connected_braces: continue
                              
        tf_max = 0
        #For each load case, calculate the transfer force and append to tf_LC
        for load_case in LC_range:
            #Skip load case if it is not present in the structure data file
            if not load_case in beam_data[beam_tf].fx_s: continue
            #Check if the user-specified node is at beam start or beam end:
            if node_tf == beam_data[beam_tf].start:
                tf = beam_data[beam_tf].fx_s[load_case]
            else:
                tf = beam_data[beam_tf].fx_e[load_case]
            # For each connected brace member, add component of axial force to transfer force
            for brace in connected_braces:
                cos_angle = np.cos(np.deg2rad(beam_data[brace].get_angle(beam_tf, beam_data)))
                if beam_data[brace].shared_node(node_tf) == 0:
                    tf += (beam_data[brace].fx_s[load_case]) * cos_angle
                else:
                    tf += (beam_data[brace].fx_e[load_case]) * cos_angle
            if abs(tf) > tf_max:
                tf_max = round(abs(tf), 3)
                LC_max = load_case

        #Find maximum transfer force out of all the load cases
        if node_tf == beam_data[beam_tf].start:
            # beam_data[beam_tf].tf_start = tf_max
            # beam_data[beam_tf].tf_LC_start = LC_max
            location = 'start'
        else:
            # beam_data[beam_tf].tf_end = tf_max
            # beam_data[beam_tf].tf_LC_end = LC_max
            location = 'end'
        beam_tf_list.append([beam_tf, location, tf_max, LC_max])
    return beam_tf_list