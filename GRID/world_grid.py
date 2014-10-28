#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros, linspace
import numpy as np
import random

from grid_filter_gl import Grid

class WorldGrid:
	
	def __init__(self):
		self.DEFAULT_PRIOR = 0.1
		self.MAP_WIDTH = 800
		self.MAP_HEIGHT = 800
		self.NUM_SPOTS = 5
		self.DIFF = 50
		
		self.potentials = []
		
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
	
	def getPartialGrid(self):
		x = 0
		y = 0
		result = []
		while x < self.MAP_WIDTH /2:
			print "x: ", x
			while y < self.MAP_HEIGHT /2:
				print "y: ", y
				pos = (x,y)
				if self.isUnvisited(pos):
					print "adding ", pos
					result.append(pos)
				y += self.DIFF
			x += self.DIFF
		print "Partial Grid: ", result
		return result
	
	def getNewUnvistedLocation(self):
		positions = self.getPartialGrid()
		i = random.randrange(len(positions))
		return positions[i]
		
	
	def isUnvisited(self, pos):
		x, y = pos
		i, j = self.coordinates_to_indexes(x, y)
		
		value = self.grid[x,y]
		value2 = self.grid[i,j]
		value3 = self.grid[j, i]
		value4 = self.grid[y,x]

		#print "(", i, ",", j, ") = ", value4
		print "(", x, ",", y, ") = ", value3
		#print "(", i, ",", j, ") = ", value2
		#print "(", x, ",", y, ") = ", value
		if value3 == self.DEFAULT_PRIOR:
			return True
		return False
		
	def getTargetLocations(self):
		print "getting locations!"
		while len(self.potentials) < self.NUM_SPOTS:
			self.potentials.append(self.getNewUnvistedLocation())
		
		for i in range(0, self.NUM_SPOTS - 1):
			pos = self.potentials[i]
			if not self.isUnvisited(pos):
				self.potentials[i] = self.getNewUnvistedLocation() 
		return self.potentials
