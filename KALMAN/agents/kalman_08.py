#!/usr/bin/python -tt

#################################################################
# After starting the bzrflag server, this is one way to start
# this code:
# python agent0.py [hostname] [port]
#
# Often this translates to something like the following (with the
# port name being printed out by the bzrflag server):
# python agent0.py localhost 49857
#################################################################

import sys
import math
import time
import random

from bzrc import BZRC, Command
from numpy import linspace
import numpy as np

class Agent(object):
	"""Class handles all command and control logic for a teams tanks."""

	def __init__(self, bzrc):
		self.bzrc = bzrc
		self.constants = self.bzrc.get_constants()
		self.commands = []
		self.ALPHA = 0.01
		self.BETA = 0.3
		self.OBS_TOLERANCE = 35.0
		self.S = 50
		self.goalradius = 30
		
		self.tankradius = 5
		self.avoidradius = 50
		self.avoidBETA = 0.1
		
		self.aimtolerance = math.pi/20
		
		self.num_ticks = 0
		self.MAXTICKS = 3000
		self.UPTICKS = 20
		self.DEBUGTICKS = 400

		self.rho = 0.3
		
		self.COLORS = ['blue','red','green','purple']
		self.color_index = 0
		
		DELTA_T = 0.005
		self.DELTA_T = DELTA_T
		self.I = np.matrix([[1, 0, 0, 0, 0, 0],[0, 1, 0, 0, 0, 0],[0, 0, 1, 0, 0, 0],[0, 0, 0, 1, 0, 0],[0, 0, 0, 0, 1, 0],[0, 0, 0, 0, 0, 1]])
		self.SIGMA_X = np.matrix('25 0;0 25')
		self.SIGMA_Z = np.matrix([[0.1, 0, 0, 0, 0, 0],[0, 0.2, 0, 0, 0, 0],[0, 0, 90, 0, 0, 0],[0, 0, 0, 0.1, 0, 0],[0, 0, 0, 0, 0.2, 0],[0, 0, 0, 0, 0, 90]])
		self.SIGMA_0 = np.matrix([[90, 0, 0, 0, 0, 0],[0, 0.1, 0, 0, 0, 0],[0, 0, 0.1, 0, 0, 0],[0, 0, 0, 90, 0, 0],[0, 0, 0, 0, 0.1, 0],[0, 0, 0, 0, 0, 0.1]])
		self.SIGMA_T = self.SIGMA_0
		self.H = np.matrix('1 0 0 0 0 0;0 0 0 1 0 0')
		self.H_t = self.H.getT()
		self.F = np.matrix([[1, DELTA_T, (DELTA_T**2) / 2, 0, 0, 0], [0, 1, DELTA_T, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 1, DELTA_T, (DELTA_T**2) / 2], [0, 0, 0, 0, 1, DELTA_T], [0, 0, 0, 0, 0, 1]])
		self.F_t = self.F.getT()
		self.mu = np.matrix('1;0;0;1;0;0')
		
		self.make_map = GnuPlot(self, self.SIGMA_X, self.mu, self.rho) 

	def tick(self, time_diff):
		"""Some time has passed; decide what to do next."""
		
		mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
		self.mytanks = mytanks
		self.othertanks = othertanks
		self.flags = [flag for flag in flags if flag.color != self.constants['team']]
		self.shots = shots
		self.enemies = [tank for tank in othertanks if tank.color !=
						self.constants['team']]
		self.obstacles = self.bzrc.get_obstacles()
		self.commands = []		
		
		
		for tank in mytanks:
			self.kalman(tank)
		
		if self.num_ticks % self.UPTICKS == 0:
			self.make_map.update_mu(self.mu_x, self.mu_y)
			self.make_map.add_animation()
		
		if self.num_ticks % self.MAXTICKS == 0:			
			self.make_map.generateGnuMap()		

		results = self.bzrc.do_commands(self.commands)
		self.num_ticks = self.num_ticks + 1

	def kalman(self, tank):
		target = self.get_target_loc(tank)
		X = np.matrix([target.x, target.y])
		if target != None:
			
			P_k = self.get_Pk()
			K = self.get_K(P_k)
			self.mu = self.F * self.mu + K * (X - self.H * self.F * self.mu)
			self.SIGMA_T = (self.I - K * self.H) * P_k
			
			mu_x = self.mu[0,0]
			mu_y = self.mu[3,0]
			
			if self.num_ticks % self.DEBUGTICKS == 0:
				print 'target: x=', target.x, ", y=",target.y
				print 'mu:\n', self.mu
			
			#calculate angle
			delta_x, delta_y, magnitude = self.calculate_objective_delta(tank.x, tank.y, mu_x, mu_y)
			turn_angle = math.atan2(delta_y, delta_x)
			relative_angle = self.normalize_angle(turn_angle - tank.angle)
			
			command = Command(tank.index, 0, 2 * relative_angle, True)
			self.commands.append(command)

	def get_Pk(self):
		P_k = self.F * self.SIGMA_T * self.F_t + self.SIGMA_Z
		return P_k
		
	def get_K(self, P_k):
		K = P_k * self.H_t * np.linalg.inv(self.H * P_k * self.H_t + self.SIGMA_X)
		return K

	def get_target_loc(self, tank):
		target = None
		color = self.get_target_color()
		if color == None:
			return None
		
		for flag in self.flags:
			if flag.color == color:
				target = flag
		
		self.mu_x = target.x
		self.mu_y = target.y
		return target
		
	def get_target_color(self):
		if self.color_index == self.constants['team']:
			self.color_index = self.color_index + 1
		
		if self.color_index > 3:
			return None
		
		anyliving = False
		for tank in self.enemies:
			if tank.color == self.COLORS[self.color_index] and tank.status == 'alive':
				anyliving = True
		
		if anyliving:
			return self.COLORS[self.color_index]
		else:
			self.color_index = self.color_index + 1
			return self.get_target_color()

	def get_best_flag(self, x, y):
		best_flag = None
		best_dist = 2 * float(self.constants['worldsize'])
		for flag in self.flags:
			dist = math.sqrt((flag.x - x)**2 + (flag.y - y)**2)
			if dist < best_dist:
				best_dist = dist
				best_flag = flag
		return best_flag
		
		
	def calculate_enemies_delta(self, my_x, my_y, enemies):
		delta_x = 0
		delta_y = 0
		
		for tank in enemies:
			dx, dy = self.avoid_target(my_x, my_y, tank.x, tank.y)
			delta_x += dx
			delta_y += dy
		
		sqnorm = math.sqrt(delta_x**2 + delta_y**2)
		
		if sqnorm == 0:
			delta_x = 0
			delta_y = 0
		else:
			delta_x = delta_x / sqnorm
			delta_y = delta_y / sqnorm
		
		return delta_x, delta_y

	def calculate_objective_delta(self, my_x, my_y, target_x, target_y):
		goal_dist = math.sqrt((target_x - my_x)**2 + (target_y - my_y)**2)
		target_angle = math.atan2(target_y - my_y, target_x - my_x)
		
		delta_xG = self.ALPHA * goal_dist * math.cos(target_angle) # r = 0
		delta_yG = self.ALPHA * goal_dist * math.sin(target_angle) # r = 0
		
		sqnorm = math.sqrt(delta_xG**2 + delta_yG**2)
		
		#set magnitude
		magnitude = 0
		if goal_dist > self.goalradius:
			magnitude = 1
		else:
			magnitude = sqnorm
		
		if sqnorm == 0:
			delta_xG = 0
			delta_yG = 0
		else:
			delta_xG = delta_xG / sqnorm
			delta_yG = delta_yG / sqnorm
			
		return delta_xG, delta_yG, magnitude

	
	def normalize_angle(self, angle):
		"""Make any angle be between +/- pi."""
		angle -= 2 * math.pi * int (angle / (2 * math.pi))
		if angle <= -math.pi:
			angle += 2 * math.pi
		elif angle > math.pi:
			angle -= 2 * math.pi
		return angle

class Tank(object):
	pass

class GnuPlot():
	
	def __init__(self, agent, SIGMA_X, mu, rho):
		self.agent = agent
		self.bzrc = agent.bzrc
		
		self.FILENAME = 'plot.gpi'
		self.WORLDSIZE = 800

		self.sigma_x = SIGMA_X[0,0]
		self.sigma_y = SIGMA_X[1,1]
		self.mu_x = mu[0,0]
		self.mu_y = mu[3,0]
		self.rho = rho
		
		self.output = ''
	
	
	def update_mu(self, mu_x, mu_y):
		self.mu_x = mu_x
		self.mu_y = mu_y
		
	def add_animation(self):
		self.output += self.gnuplot_variables(self.sigma_x, self.sigma_y, self.mu_x, self.mu_y, self.rho)
		self.output += 'splot 1.0/(2.0 * pi * sigma_x * sigma_y * sqrt(1 - rho**2) ) \
		* exp(-1.0/(2.0 * (1 - rho**2)) * ((x - mu_x)**2 / sigma_x**2 + (y - mu_y)**2 / sigma_y**2 \
		- 2.0*rho*(x-mu_x)*(y-mu_y)/(sigma_x*sigma_y) ) ) with pm3d\n'
		self.output += 'pause 0.1\n'
	
	def generateGnuMap(self):
		outfile = open(self.FILENAME, 'w')
		minimum = -self.WORLDSIZE / 2
		maximum = self.WORLDSIZE / 2
		print >>outfile, self.gnuplot_header(minimum, maximum)
		print >>outfile, 'set palette model RGB functions 1-gray, 1-gray, 1-gray\n'
		print >>outfile, 'set isosamples 100\n'
		print >>outfile, self.output
		self.output = ''

		outfile.close()
	
	def gnuplot_header(self, minimum, maximum):
		'''Return a string that has all of the gnuplot sets and unsets.'''
		s = ''
		s += 'set xrange [%s: %s]\n' % (minimum, maximum)
		s += 'set yrange [%s: %s]\n' % (minimum, maximum)
		s += 'set pm3d\n'
		s += 'set view map\n'
		# The key is just clutter.  Get rid of it:
		s += 'unset key\n'
		# Make sure the figure is square since the world is square:
		s += 'set size square\n'
		# Add a pretty title (optional):
		s += "set title 'Kalman Filter'\n"
		return s
	
	def gnuplot_variables(self, sigma_x, sigma_y, mu_x, mu_y, rho):
		s = ''
		s += 'sigma_x = {}\n'.format(sigma_x)
		s += 'sigma_y = {}\n'.format(sigma_y)
		s += 'mu_x = {}\n'.format(mu_x)
		s += 'mu_y = {}\n'.format(mu_y)
		s += 'rho = {}\n'.format(rho)
		return s

def main():
	# Process CLI arguments.
	try:
		execname, host, port = sys.argv
	except ValueError:
		execname = sys.argv[0]
		print >>sys.stderr, '%s: incorrect number of arguments' % execname
		print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
		sys.exit(-1)

	# Connect.
	#bzrc = BZRC(host, int(port), debug=True)
	bzrc = BZRC(host, int(port))

	agent = Agent(bzrc)

	prev_time = time.time()
	cur_time = time.time()
	# Run the agent
	try:
		while True:
			cur_time = time.time()
			time_diff = cur_time - prev_time
			prev_time = cur_time
			#time_diff = time.time() - prev_time
			agent.tick(time_diff)
	except KeyboardInterrupt:
		print "Exiting due to keyboard interrupt."
		bzrc.close()


if __name__ == '__main__':
	main()

# vim: et sw=4 sts=4
