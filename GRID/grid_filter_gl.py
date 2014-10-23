#!/usr/bin/env python

import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from numpy import zeros

class Grid:
	
	#grid = None
	
	def __init__(self):
		self.grid = None
		

	def draw_grid(self):
		# This assumes you are using a numpy array for your grid
		width, height = self.grid.shape
		glRasterPos2f(-1, -1)
		glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, self.grid)
		glFlush()
		glutSwapBuffers()

	def update_grid(self, new_grid):
		#global grid
		self.grid = new_grid



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



# vim: et sw=4 sts=4
