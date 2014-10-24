#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros

class WorldGrid:
	
	#grid = None
	
	def __init__(self):
		self.DEFAULT_PRIOR = 0.1
		self.MAP_WIDTH = 800
		self.MAP_HEIGHT = 800
		
		self.grid = zeros(self.MAP_WIDTH, self.MAP_HEIGHT)
		self.grid.fill(DEFAULT_PRIOR)

	def coordinates_to_indexes(self, x, y):
		i = x + (MAP_WIDTH / 2)
		j = y - (MAP_HEIGHT / 2)
		return i, j
		
	def grid_to_indexes(self, grid_x, grid_y, pos):
		origin_x, origin_y = pos
		offset_x = grid_x + origin_x
		offset_y = grid_y + origin_y
		x,y = self.coordinates_to_indexes(offset_x, offset_y)
		return x,y
		
	def get_world_value(self, grid_x, grid_y, pos):
		x,y = self.grid_to_indexes(self, grid_x, grid_y, pos)
		return self.grid[x,y]
		
	def set_world_value(self, grid_x, grid_y, pos, value)
		x,y = self.grid_to_indexes(self, grid_x, grid_y, pos)
		self.grid[x,y] = value

