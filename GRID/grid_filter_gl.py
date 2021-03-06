#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros
import numpy as np

class Grid:
	
	#grid = None
	
	def __init__(self):
		self.grid = None
		#self.world = WorldGrid()
		

	def draw_grid(self, points):
		# This assumes you are using a numpy array for your grid
		width, height = self.grid.shape
		
		targets = zeros((width, height))
		
		for pos in points:
			self.set_surrounding_pixels(targets, pos)
			
		draw = self.grid+targets
		
		glRasterPos2f(-1, -1)
		glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, draw)
		glFlush()
		glutSwapBuffers()

	def update_grid(self, new_grid):
		#global grid
		self.grid = new_grid

	def set_surrounding_pixels(self, targets, pos):
		x1,y1 = pos
		y,x = self.coordinates_to_indexes(x1, y1)
		print "printing target ", x, ",", y
		targets[x-1,y-1] = 1
		targets[x,y-1] = 1
		targets[x+1,y-1] = 1
		targets[x,y-1] = 1
		targets[x,y] = 1
		targets[x,y+1] = 1
		targets[x+1,y-1] = 1
		targets[x+1,y] = 1
		targets[x+1,y+1] = 1

	def init_window(self, width, height):
		global window
		#global grid
		self.grid = zeros((width, height))
		glutInit(())
		glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
		glutInitWindowSize(width, height)
		glutInitWindowPosition(0, 0)
		window = glutCreateWindow("Grid filter")
		glutDisplayFunc(self.draw_grid)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		#glutMainLoop()

	def coordinates_to_indexes(self, x, y):
		width, height = self.grid.shape
		
		i = x + (width / 2)
		j = y - (height / 2)
		return i, j


# vim: et sw=4 sts=4
