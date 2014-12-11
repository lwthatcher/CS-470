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
		self.shotspeed = self.constants['shotspeed']
		self.shotrange = self.constants['shotrange']
		self.commands = []
		self.ALPHA = 0.01
		self.goalradius = 30
		
<<<<<<< HEAD
		self.num_ticks = 1
		self.MAXTICKS = 5000
=======
		self.num_ticks = 0
		self.RESET = 5000
		self.PRINTICKS = 50
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42
		self.UPTICKS = 20

		self.rho = 0.3
		
		self.COLORS = ['blue','red','green','purple']
		self.color_index = 0
		self.color_changed = True
		
		DELTA_T = 0.005
		self.DELTA_T = DELTA_T
		self.I = np.matrix([[1, 0, 0, 0, 0, 0],[0, 1, 0, 0, 0, 0],[0, 0, 1, 0, 0, 0],[0, 0, 0, 1, 0, 0],[0, 0, 0, 0, 1, 0],[0, 0, 0, 0, 0, 1]])
		self.SIGMA_X = np.matrix('25 0;0 25')
		self.SIGMA_Z = np.matrix([[0.1, 0, 0, 0, 0, 0],[0, 0.2, 0, 0, 0, 0],[0, 0, 50, 0, 0, 0],[0, 0, 0, 0.1, 0, 0],[0, 0, 0, 0, 0.2, 0],[0, 0, 0, 0, 0, 50]])
		self.SIGMA_0 = np.matrix([[90, 0, 0, 0, 0, 0],[0, 0.1, 0, 0, 0, 0],[0, 0, 0.1, 0, 0, 0],[0, 0, 0, 90, 0, 0],[0, 0, 0, 0, 0.1, 0],[0, 0, 0, 0, 0, 0.1]])
		self.SIGMA_T = self.SIGMA_0
		self.H = np.matrix('1 0 0 0 0 0;0 0 0 1 0 0')
		self.H_t = self.H.getT()
		self.F = np.matrix([[1, DELTA_T, (DELTA_T**2) / 2, 0, 0, 0], [0, 1, DELTA_T, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 1, DELTA_T, (DELTA_T**2) / 2], [0, 0, 0, 0, 1, DELTA_T], [0, 0, 0, 0, 0, 1]])
		self.F_t = self.F.getT()
		self.mu = np.matrix('1;0;0;1;0;0')
		
		self.make_map = GnuPlot(self, self.SIGMA_T, self.mu) 
<<<<<<< HEAD
=======
		
		self.file_index = 0
		
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42

	def tick(self, time_diff):
		"""Some time has passed; decide what to do next."""
		
		mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
		self.mytanks = mytanks
		#self.othertanks = othertanks
		self.flags = [flag for flag in flags if flag.color != self.constants['team']]
		#self.shots = shots
		self.enemies = [tank for tank in othertanks if tank.color !=
						self.constants['team']]
		self.obstacles = self.bzrc.get_obstacles()
		self.commands = []		
		
		if self.num_ticks % self.PRINTICKS == 0:
			print self.file_index
			self.make_map.update_file_index(self.file_index)
			self.file_index = self.file_index + 1	
			self.make_map.generateGnuMaps()
		
		for tank in self.mytanks:
			self.kalman(tank)
		
		if self.num_ticks % self.UPTICKS == 0:
<<<<<<< HEAD
			self.make_map.update_mu(self.mu_x, self.mu_y)
			self.make_map.update_sigma(self.SIGMA_T)
			self.make_map.add_animation()
			print self.enemies[1].callsign
		
		if self.num_ticks % self.MAXTICKS == 0:	
			self.reset()
			print "printing map"		
			self.make_map.generateGnuMap()		
=======
			self.make_map.update_observed_position(self.observed_position)
			self.make_map.update_predicted_position(self.predicted_position)
			self.make_map.update_mu(self.mu[0,0], self.mu[3,0])
			self.make_map.update_sigma(self.SIGMA_T)
			#self.make_map.add_animation()
			
		if self.num_ticks % self.RESET == 0:
			self.reset()	
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42

		results = self.bzrc.do_commands(self.commands)
		self.num_ticks = self.num_ticks + 1

	def kalman(self, tank):
		sensor = self.get_target_loc()
		
		if sensor != None:
			X = np.matrix([[sensor.x],[sensor.y]])
			P_k = self.get_Pk()
			K = self.get_K(P_k)
			self.mu = self.F * self.mu + K * (X - self.H * self.F * self.mu)		
			self.SIGMA_T = (self.I - K * self.H) * P_k
			
			current_shot_dist = self.get_target_dist(tank.x, tank.y, sensor.x, sensor.y)
			
			iterations = 0
			if current_shot_dist <= self.shotrange:
				iterations = int(current_shot_dist)
			target_position = self.predict_future_position(iterations)

			#calculate angle
			delta_x, delta_y, magnitude = self.calculate_objective_delta(tank.x, tank.y, target_position[0,0], target_position[3,0])
			turn_angle = math.atan2(delta_y, delta_x)
			relative_angle = self.normalize_angle(turn_angle - tank.angle)
			
			if abs(relative_angle) < 0.001:
				command = Command(tank.index, 0, 2 * relative_angle, False)
				#print "relative_angle", relative_angle
			else:
				command = Command(tank.index, 0, 2 * relative_angle, True)
			self.commands.append(command)
		else:
			self.victory_lap(tank)

	def predict_future_position(self, iterations):
		future_position = self.F * self.mu
		
		for i in range(1, iterations):
			future_position = self.F * future_position
		
		return future_position
	
	def get_target_dist(self, tank_x, tank_y, target_x, target_y):
		dist = math.sqrt((tank_x - target_x)**2 + (tank_y - target_y)**2)
		return dist
	
	def get_Pk(self):
		P_k = self.F * self.SIGMA_T * self.F_t + self.SIGMA_Z
		return P_k
		
	def get_K(self, P_k):
		K = P_k * self.H_t * np.linalg.inv(self.H * P_k * self.H_t + self.SIGMA_X)
		return K

	def reset(self):
		self.SIGMA_T = self.SIGMA_0
	
	def get_target_loc(self):
		target = None
		color, tank = self.get_target_color()
		if color == None:
			return None
		
		if self.color_changed:
			#set flag as target (reset sigma)
			for flag in self.flags:
				if flag.color == color:
					target = flag
			self.color_changed = False
		else:
			#set enemy tank as target
			target = tank
		
		self.mu_x = target.x
		self.mu_y = target.y
		return target
		
	def get_target_color(self):
		if self.color_index == self.constants['team']:
			self.color_index = self.color_index + 1
			self.color_changed = True
		
		if self.color_index > 3:
			return None, None
		
		anyliving = False
		TargetTank = None
		for tank in self.enemies:
			if tank.color == self.COLORS[self.color_index] and tank.status == 'alive':
				anyliving = True
				TargetTank = tank
		
		if anyliving:
			return self.COLORS[self.color_index], TargetTank
		else:
			self.color_index = self.color_index + 1
			self.color_changed = True
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

	def victory_lap(self, tank):
		relative_angle = 0.5
		command = Command(tank.index, 1, 2 * relative_angle, True)

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
	
	def __init__(self, agent, SIGMA_T, mu):
		self.agent = agent
		self.bzrc = agent.bzrc
		
<<<<<<< HEAD
		self.FILENAME = 'plot.gpi'
=======
		self.MU_FILE = 'mu.dat'
		self.PRED_FILE = 'prediction.dat'
		self.OBS_FILE = 'obs.dat'
		
		self.VAR_FILE = 'var.gpi'
		self.POINTS_FILE = 'points.gpi'
		self.SIGMA_FILE = 'sigma.txt'
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42
		self.WORLDSIZE = 800

		self.update_sigma(SIGMA_T)		

		self.mu_x = mu[0,0]
		self.mu_y = mu[2,0]
		
<<<<<<< HEAD
		self.output = ''	
=======
		self.prediction_x = 1
		self.prediction_y = 1
		
		self.observed_x = 1
		self.observed_y = 1
		
		self.output = ''
	
	def update_file_index(self, index):
		self.VAR_FILE = 'GnuVariance/var{}.gpi'.format(index)
		self.POINTS_FILE = 'GnuPoints/points{}.gpi'.format(index)
		self.SIGMA_FILE = 'GnuSigma/sigma{}.txt'.format(index)
	
	def update_observed_position(self, observation):
		self.observed_x = observation[0,0]
		self.observed_y = observation[1,0]
	
	def update_predicted_position(self, prediction):
		self.prediction_x = prediction[0,0]
		self.prediction_y = prediction[3,0]
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42
	
	def update_mu(self, mu_x, mu_y):
		self.mu_x = mu_x
		self.mu_y = mu_y
		
	def update_sigma(self, SIGMA_T):
		self.SIGMA_T = SIGMA_T
		self.sigma_x = self.get_sigma_x()
		self.sigma_y = self.get_sigma_y()
		self.rho = self.get_rho()		
		
	def get_sigma_x(self):
		var_x = self.SIGMA_T[0,0]
		sigma_x = math.sqrt(var_x)
		return sigma_x
		
	def get_sigma_y(self):
		var_y = self.SIGMA_T[3,3]
		sigma_y = math.sqrt(var_y)
		return sigma_y
		
	def get_rho(self):
		sigma_x = self.get_sigma_x()
		sigma_y = self.get_sigma_y()
		sigma_xy = self.SIGMA_T[3,0]
		rho = sigma_xy / (sigma_x * sigma_y)
		return rho
		
	def add_animation(self):
		self.output += self.gnuplot_variables(self.sigma_x, self.sigma_y, self.mu_x, self.mu_y, self.rho)
		self.output += 'splot 1.0/(2.0 * pi * sigma_x * sigma_y * sqrt(1 - rho**2) ) \
		* exp(-1.0/(2.0 * (1 - rho**2)) * ((x - mu_x)**2 / sigma_x**2 + (y - mu_y)**2 / sigma_y**2 \
		- 2.0*rho*(x-mu_x)*(y-mu_y)/(sigma_x*sigma_y) ) ) with pm3d\n'
		self.output += 'pause 0.1\n'
	
<<<<<<< HEAD
	def generateGnuMap(self):
		outfile = open(self.FILENAME, 'w')
		minimum = -self.WORLDSIZE / 2
		maximum = self.WORLDSIZE / 2
		print >>outfile, self.gnuplot_header(minimum, maximum)
		print >>outfile, 'set palette model RGB functions 1-gray, 1-gray, 1-gray\n'
		print >>outfile, 'set isosamples 100\n'
		print >>outfile, self.output
		self.output = ''
=======
	def generateGnuMaps(self):
		self.generateVarianceMap()
		self.generatePointsMap()
		self.generateVarianceVals()
		self.appendPointsData()
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42

	def generateVarianceVals(self):
		outfile = open(self.SIGMA_FILE, 'w')
		print >>outfile, 'var_x = {}\n'.format(self.SIGMA_T[0,0])
		print >>outfile, 'var_y = {}'.format(self.SIGMA_T[3,3])
		outfile.close()
<<<<<<< HEAD
=======
	
	def generatePointsMap(self):
		outfile = open(self.POINTS_FILE, 'w')
		minimum = -self.WORLDSIZE / 2
		maximum = self.WORLDSIZE / 2
		
		print >>outfile, self.gnuplot_points_header(minimum, maximum)
		print >>outfile, self.gnuplot_points()
		outfile.close()
	
	def generateVarianceMap(self):
		outfile = open(self.VAR_FILE, 'w')
		minimum = -self.WORLDSIZE / 2
		maximum = self.WORLDSIZE / 2
		print >>outfile, self.gnuplot_var_header(minimum, maximum)
		print >>outfile, 'set palette model RGB functions 1-gray, 1-gray, 1-gray\n'
		print >>outfile, 'set isosamples 100\n'
		print >>outfile, self.output
		self.output = ''

		outfile.close()
	
	def appendPointsData(self):
		self.update_mu_file()
		self.update_prediction_file()
		self.update_observed_file()

	def update_mu_file(self):
		mu_outfile = open(self.MU_FILE, 'a')
		print >>mu_outfile, '{}\t{}'.format(self.mu_x, self.mu_y)
		mu_outfile.close()
		
	def update_prediction_file(self):
		pred_output = open(self.PRED_FILE, 'a')
		print >>pred_output, '{}\t{}'.format(self.prediction_x, self.prediction_y)
		pred_output.close()
		
	def update_observed_file(self):
		obs_outfile = open(self.OBS_FILE, 'a')
		print >>obs_outfile, '{}\t{}'.format(self.observed_x, self.observed_y)
		obs_outfile.close()
	
	def gnuplot_points_header(self, minimum, maximum):
		s = ''
		s += 'set xrange [%s: %s]\n' % (minimum, maximum)
		s += 'set yrange [%s: %s]\n' % (minimum, maximum)
		s += 'set view map\n'
		# The key is just clutter.  Get rid of it:
		#s += 'unset key\n'
		# Make sure the figure is square since the world is square:
		s += 'set size square\n'
		# Add a pretty title (optional):
		s += "set title 'Kalman Filter (Positions)'\n"
		return s
>>>>>>> 94a0f4c5627e51ca25e420fd27d26987159e3e42
	
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
<<<<<<< HEAD
		s += "set title 'Kalman Filter'\n"
=======
		s += "set title 'Kalman Filter (Variance)'\n"
		return s
	
	
	def gnuplot_points(self):
		s = ''
		s += 'plot "<echo \'{} {}\'" with points ls 1,'.format(self.observed_x, self.observed_y)
		s += ' "<echo \'{} {}\'" with points ls 2,'.format(self.mu_x, self.mu_y)
		s += ' "<echo \'{} {}\'" with points ls 3'.format(self.prediction_x, self.prediction_y)
>>>>>>> 6e29a3b79444a21ae58bf0c20a0ec947bf76d67c
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
