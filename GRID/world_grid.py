#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros, linspace
import numpy as np

from grid_filter_gl import Grid

class WorldGrid:
	
	def __init__(self):
		self.DEFAULT_PRIOR = 0.1
		self.MAP_WIDTH = 800
		self.MAP_HEIGHT = 800
		
		self.grid = np.zeros((self.MAP_WIDTH, self.MAP_HEIGHT))
		self.grid.fill(self.DEFAULT_PRIOR)
		
		self.draw_grid = Grid()
		self.draw_grid.init_window(800, 800)

	def coordinates_to_indexes(self, x, y):
		i = x + (self.MAP_WIDTH / 2)
		j = y - (self.MAP_HEIGHT / 2)
		return i, j
		
	def grid_to_indexes(self, grid_x, grid_y, pos):
		origin_x, origin_y = pos
		offset_x = grid_x + origin_x
		offset_y = grid_y + origin_y
		x, y = self.coordinates_to_indexes(offset_x, offset_y)
		return y, x
		
	def get_world_value(self, grid_x, grid_y, pos):
		x,y = self.grid_to_indexes(grid_x, grid_y, pos)
		return self.grid[x,y]
		
	def set_world_value(self, grid_x, grid_y, pos, value):
		x,y = self.grid_to_indexes(grid_x, grid_y, pos)
		self.grid[x,y] = value
		
	def draw_obstacle_grid(self):
		self.draw_grid.update_grid(self.grid)
		self.draw_grid.draw_grid();
		

