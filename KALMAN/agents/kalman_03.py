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
		self.wroteonce = False
		self.goalradius = 30
		
		self.tankradius = 5
		self.avoidradius = 50
		self.avoidBETA = 0.1
		
		self.aimtolerance = math.pi/20
		
		self.num_ticks = 0
		self.MAXTICKS = 100
		self.sigma_x = 25
		self.sigma_y = 25
		self.mu_x = 0
		self.mu_y = 0
		self.rho = 0.3
		
		self.COLORS = ['blue','red','green','purple']
		self.color_index = 0
		
		self.DELTA_T = 0.005

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
		
		print(self.enemies)
		
		for tank in self.enemies:
			pass
		
		
		make_map = GnuPlot(self, self.sigma_x, self.sigma_y, self.mu_x, self.mu_y, self.rho) 
		
		if not self.wroteonce:
			make_map.generateGnuMap()
			self.wroteonce = True

		
		for tank in mytanks:
			self.kalman(tank)
		

		results = self.bzrc.do_commands(self.commands)
		self.num_ticks = self.num_ticks + 1

	def kalman(self, tank):
		target = self.get_target_loc(tank)
		if target != None:
			
			#calculate angle
			delta_x, delta_y, magnitude = self.calculate_objective_delta(tank.x, tank.y, target.x, target.y)
			turn_angle = math.atan2(delta_y, delta_x)
			relative_angle = self.normalize_angle(turn_angle - tank.angle)
			
			command = Command(tank.index, 0, 2 * relative_angle, True)
			self.commands.append(command)


	def get_target_loc(self, tank):
		target = None
		color = self.get_target_color()
		if color == None:
			return None
		
		for flag in self.flags:
			if flag.color == color:
				target = flag
		
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
		
	def avoid_target(self, my_x, my_y, target_x, target_y):
		goal_dist = math.sqrt((target_x - my_x)**2 + (target_y - my_y)**2)
		target_angle = math.atan2(target_y - my_y, target_x - my_x)
		
		dx = 0
		dy = 0
		
		s = self.avoidradius
		r = self.tankradius
		
		if goal_dist < self.tankradius:
			dx = -1 * math.cos(target_angle) * 1000 #infinity
			dy = -1 * math.sin(target_angle) * 1000 #infinity
		elif goal_dist >= self.tankradius and goal_dist <= (s + r):
			dx = -1 * self.avoidBETA * (s + r - goal_dist) * math.cos(target_angle)
			dy = -1 * self.avoidBETA * (s + r - goal_dist) * math.sin(target_angle)
		else:
			dx = 0
			dy = 0
		return dx, dy
		
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

		
	def should_fire(self, tank):
		for enemy in self.enemies:
			target_angle = math.atan2(enemy.y - tank.y, enemy.x - tank.x)
			if abs(tank.angle - target_angle) < self.aimtolerance:
				return True
				
		return False

	def move_to_position(self, tank, target_x, target_y):
		"""Set command to move to given coordinates."""
		
		#get deltas
		delta_xG, delta_yG, magnitude = self.calculate_objective_delta(tank.x, tank.y, target_x, target_y)
		delta_xO, delta_yO = self.calculate_obstacles_delta(tank.x, tank.y)
		delta_xR, delta_yR = self.calculate_random_delta()
		delta_xA, delta_yA = self.calculate_enemies_delta(tank.x, tank.y, self.enemies)
		
		#combine
		delta_x = delta_xG + delta_xO + delta_xR + delta_xA
		delta_y = delta_yG + delta_yO + delta_yR + delta_xA
		
		#calculate angle
		turn_angle = math.atan2(delta_y, delta_x)
		relative_angle = self.normalize_angle(turn_angle - tank.angle)
		
		#put lower bound on speed: no slower than 40%
		if magnitude < 0.4:
			magnitude = 0.4
			
		fire = self.should_fire(tank)
		
		command = Command(tank.index, magnitude, 2 * relative_angle, fire)
		self.commands.append(command)
	
	def get_obstacle_force(self, obstacle, x, y):
		
		delta_x = 0 
		delta_y = 0
		
		big_num = 5000
		
		min_x = big_num
		max_x = -big_num
		min_y = big_num
		max_y = -big_num
		
		for p in obstacle:
			repel_x, repel_y = self.get_tangential_field(x, y, p)
			delta_x += repel_x
			delta_y += repel_y
			
			xp, yp = p
			if xp < min_x:
				min_x = xp
			elif xp > max_x:
				max_x = xp
			
			if yp < min_y:
				min_y = yp
			elif yp > max_y:
				max_y = yp
		
		center_point = [(min_x + min_y) / 2,  (min_y + max_y) / 2]
		
		repel_x, repel_y = self.get_repel_field(x, y, center_point[0], center_point[1]) # repel from the center of the box
		delta_x += repel_x
		delta_y += repel_y
				
		return delta_x, delta_y
	
	def get_tangential_field(self, x, y, p):
		my_x = x
		my_y = y
		xO, yO = p
		
		dist = math.sqrt( (my_x - xO)**2 + (my_y - yO)**2 )
		
		if dist < self.OBS_TOLERANCE:
			
			# angle between the tank and the obstacle
			theta = math.atan2(yO - y, xO - x) + math.pi / 2

			delta_x = -self.BETA * (self.avoidradius - dist) * math.cos(theta)
			delta_y = -self.BETA * (self.avoidradius - dist) * math.sin(theta)
			
			return delta_x, delta_y
		else:
			return 0, 0
	
	def get_repel_field(self, x, y, xO, yO):
		my_x = x
		my_y = y

		dist = math.sqrt( (my_x - xO)**2 + (my_y - yO)**2 )
		
		if dist < self.OBS_TOLERANCE:
			
			# angle between the tank and the obstacle
			theta = math.atan2(yO - y, xO - x)

			delta_x = -self.BETA * (self.avoidradius - dist) * math.cos(theta) # math.cos returns in radians
			delta_y = -self.BETA * (self.avoidradius - dist) * math.sin(theta)
			
			return delta_x, delta_y
		else:
			return 0, 0
	
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
	
	def __init__(self, agent, sigmax, sigmay, mu_x, mu_y, rho):
		self.agent = agent
		self.bzrc = agent.bzrc
		
		self.FILENAME = 'plot.gpi'
		self.WORLDSIZE = 800

		self.sigma_x = sigmax
		self.sigma_y = sigmay
		self.mu_x = mu_x
		self.mu_y = mu_y
		self.rho = rho
		
	
	def generateGnuMap(self):
		outfile = open(self.FILENAME, 'w')
		minimum = -self.WORLDSIZE / 2
		maximum = self.WORLDSIZE / 2
		print >>outfile, self.gnuplot_header(minimum, maximum)
		print >>outfile, 'set palette model RGB functions 1-gray, 1-gray, 1-gray\n'
		print >>outfile, 'set isosamples 100\n'
		print >>outfile, self.gnuplot_variables(self.sigma_x, self.sigma_y, self.mu_x, self.mu_y, self.rho)
		print >>outfile, 'splot 1.0/(2.0 * pi * sigma_x * sigma_y * sqrt(1 - rho**2) ) \
		* exp(-1.0/(2.0 * (1 - rho**2)) * ((x - mu_x)**2 / sigma_x**2 + (y - mu_y)**2 / sigma_y**2 \
		- 2.0*rho*(x-mu_x)*(y-mu_y)/(sigma_x*sigma_y) ) ) with pm3d\n'

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
