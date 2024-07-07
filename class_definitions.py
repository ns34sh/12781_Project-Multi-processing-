# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 23:06:26 2023

@author: namit
"""

import numpy as np


class node_class():
    def __init__(self, x, y ,z):
        self.x = x
        self.y = y
        self.z = z
        self.conn_beams = set()
        
#Code for unit_vector and angle_between functions taken from 
#https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

class beam_class():
    def __init__(self, nodeA, nodeB, node_data):
        self.start = nodeA
        self.end = nodeB
        
        self.fx_s = {}
        self.fx_e = {}
        
        #Set start and end coordinates of the beam ends
        self.sx = node_data[nodeA].x
        self.sy = node_data[nodeA].y
        self.sz = node_data[nodeA].z
        #
        self.ex = node_data[nodeB].x
        self.ey = node_data[nodeB].y
        self.ez = node_data[nodeB].z
        #
        self.tf_start = None
        self.tf_LC_start = None
        self.tf_end = None
        self.tf_LC_end = None
    
    def get_len(self):
        #Returns length of the beam
        return ((self.sx - self.ex)**2 + (self.sy - self.ey)**2 + (self.sz - self.ez)**2)**0.5
    
    def shared_node(self, node):
        #Checks if a node is a beam start node or end node or neither
        if node == self.start:
            return 0
        elif node == self.end:
            return 1
        else:
            return -1
    
    def get_angle(self, beam_obj):
        #Returns the angle between this beam and another beam
        self_v = np.array((self.ex - self.sx, self.ey - self.sy, self.ez - self.sz))
        # beam = beam_data[beam_num]
        beam= beam_obj
        beam_v = np.array((beam.ex - beam.sx, beam.ey - beam.sy, beam.ez - beam.sz))
        if self.shared_node(beam.start) == 0:
            self_v = self_v
            beam_v = beam_v
        elif self.shared_node(beam.end) == 0:
            self_v = self_v
            beam_v = -beam_v
        elif self.shared_node(beam.start) == 1:
            self_v = -self_v
            beam_v = beam_v
        elif self.shared_node(beam.end) == 1:
            self_v = -self_v
            beam_v = -beam_v
        return round(np.rad2deg(angle_between(self_v, beam_v)), 3)
    
    def is_beam(self):
        self_v = np.array((self.ex - self.sx, self.ey - self.sy, self.ez - self.sz))
        ref_ver = np.array([0, 1, 0])
        ref_hor = np.array([1, 0, 0])
        angle_ver = round(np.rad2deg(angle_between(self_v, ref_ver)), 3)
        angle_hor = round(np.rad2deg(angle_between(self_v, ref_hor)), 3)
        is_beam = False
        if abs(90 - angle_ver) <= 10 and (angle_hor <= 10 or abs(90 - angle_hor) <= 10 or abs(180 - angle_hor) <= 10):
            is_beam = True
        return is_beam
        
        


        
        
        
        
        
        
        
        
        
        