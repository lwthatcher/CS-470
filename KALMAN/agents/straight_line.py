#!/usr/bin/python -tt

# An incredibly simple agent.  All we do is find the closest enemy tank, drive
# towards it, and shoot.  Note that if friendly fire is allowed, you will very
# often kill your own tanks with this code.

#################################################################
# NOTE TO STUDENTS
# This is a starting point for you.  You will need to greatly
# modify this code if you want to do anything useful.  But this
# should help you to know how to interact with BZRC in order to
# get the information you need.
#
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
		
		self.tank_goals = []

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
		
		print(self.constants)
		
		#make_map = GnuPlot(self, self.flags, self.obstacles) 
		
		if not self.wroteonce:
			for tank in self.mytanks:
				self.tank_goals.append('CENTER')
			self.wroteonce = True
		'''
		for tank in mytanks:
			if tank.flag == '-':
				self.goto_flags(tank)
			else:
				base_x, base_y = self.get_base_center(self.get_my_base())
				self.move_to_position(tank, base_x, base_y)'''
		
		self.move_all()

		results = self.bzrc.do_commands(self.commands)

	def move_all(self):
		for tank in self.mytanks:
			self.move_forward(tank)

	def move_forward(self, tank):		
		target = self.tank_goals[tank.index]
		if target == 'CENTER':
			self.move_to_position(tank, 0, 0)
			dist_x = 0 - tank.x
			dist_y = 0 - tank.y
			if (abs(dist_x) < 10 and abs(dist_y) < 10):
				self.tank_goals[tank.index] = 'BASE'
		else: #target == 'BASE'
			base_x, base_y = self.get_base_center(self.get_my_base())
			self.move_to_position(tank, base_x, base_y)
			dist_x = base_x - tank.x
			dist_y = base_y - tank.y
			if (abs(dist_x) < 10 and abs(dist_y) < 10):
				self.tank_goals[tank.index] = 'CENTER'

	def get_my_base(self):
		mybases = [base for base in self.bzrc.get_bases() if base.color == self.constants['team']]
		mybase = mybases[0]
		return mybase
	
	def get_base_center(self, base):
		center_x = ((base.corner1_x + base.corner2_x + base.corner3_x + base.corner4_x) / 4)
		center_y = ((base.corner1_y + base.corner2_y + base.corner3_y + base.corner4_y) / 4)
		return center_x, center_y

	def goto_flags(self, tank):
		best_flag = self.get_best_flag(tank.x, tank.y)
		if best_flag is None:
			command = Command(tank.index, 0, 0, False)
			self.commands.append(command)
		else:
			self.move_to_position(tank, best_flag.x, best_flag.y)

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

	def calculate_obstacles_delta(self, x, y):
		delta_xO = 0
		delta_yO = 0
		
		for obs in self.obstacles:
			repel_xO, repel_yO = self.get_obstacle_force(obs, x, y)
			delta_xO += repel_xO
			delta_yO += repel_yO
		
		sqnorm = math.sqrt(delta_xO**2 + delta_yO**2)
			
		if sqnorm == 0:
			delta_xO = 0
			delta_yO = 0
		else:
			delta_xO = delta_xO / sqnorm
			delta_yO = delta_yO / sqnorm
		
		'''if delta_xG != 0 or delta_yG != 0:
			print "delta_xO: ", delta_xO
			print "delta_yO: ", delta_yO'''
			
		return delta_xO, delta_yO

	def calculate_random_delta(self):
		dx = random.uniform(-.01, .01)
		dy = random.uniform(-.01, .01)
		return dx, dy
		
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
		
		#combine
		delta_x = delta_xG
		delta_y = delta_yG
		
		#calculate angle
		turn_angle = math.atan2(delta_y, delta_x)
		relative_angle = self.normalize_angle(turn_angle - tank.angle)
		
		#put lower bound on speed: no slower than 40%
		if magnitude < 0.4:
			magnitude = 0.4
			
		fire = self.should_fire(tank)
		
		command = Command(tank.index, 1, 2 * relative_angle, False)
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
	
	def __init__(self, agent, flags, obstacles):
		self.agent = agent
		self.bzrc = agent.bzrc
		self.constants = self.bzrc.get_constants()
		
		self.FILENAME = 'plot.gpi'
		self.WORLDSIZE = 800
		self.SAMPLES = 50
		self.VEC_LEN = 0.75 * self.WORLDSIZE / self.SAMPLES
		
		self.flags = flags
		self.obstacles = obstacles
		
	
	def generateGnuMap(self):
		outfile = open(self.FILENAME, 'w')
		minimum = -self.WORLDSIZE / 2
		maximum = self.WORLDSIZE / 2
		print >>outfile, self.gnuplot_header(minimum, maximum)
		print >>outfile, self.draw_obstacles(self.bzrc.get_obstacles())
		field_function = self.generate_field_function(150)
		print >>outfile, self.plot_field(field_function)
		outfile.close()
		
	def generate_field_function(self, scale):
		
		tank1 = Tank()
		tank1.x = 0
		tank1.y = 150
		
		tank2 = Tank()
		tank2.x = 0
		tank2.y = -200
		
		faketanks = [tank1, tank2]
		
		def function(x, y):
			target = self.agent.get_best_flag(x, y)
			
			#get deltas
			#delta_xG, delta_yG = [0, 0]
			#magnitude = 1
			delta_xG, delta_yG, magnitude = self.agent.calculate_objective_delta(x, y, target.x, target.y)
			delta_xO, delta_yO = self.agent.calculate_obstacles_delta(x, y)
			delta_xA, delta_yA = self.agent.calculate_enemies_delta(x, y, faketanks)
			
			#combine
			delta_x = delta_xG + delta_xO + delta_xA
			delta_y = delta_yG + delta_yO + delta_yA
			
			magnitude = math.sqrt(delta_x**2 + delta_y**2)
			
			return delta_x*scale*magnitude, delta_y*scale*magnitude
			
		return function
	
	def gpi_point(self, x, y, vec_x, vec_y):
		'''Create the centered gpi data point (4-tuple) for a position and
		vector.  The vectors are expected to be less than 1 in magnitude,
		and larger values will be scaled down.'''
		r = (vec_x ** 2 + vec_y ** 2) ** 0.5
		if r > 1:
			vec_x /= r
			vec_y /= r
		return (x - vec_x * self.VEC_LEN / 2, y - vec_y * self.VEC_LEN / 2,
				vec_x * self.VEC_LEN, vec_y * self.VEC_LEN)
	
	def gnuplot_header(self, minimum, maximum):
		'''Return a string that has all of the gnuplot sets and unsets.'''
		s = ''
		s += 'set xrange [%s: %s]\n' % (minimum, maximum)
		s += 'set yrange [%s: %s]\n' % (minimum, maximum)
		# The key is just clutter.  Get rid of it:
		s += 'unset key\n'
		# Make sure the figure is square since the world is square:
		s += 'set size square\n'
		# Add a pretty title (optional):
		#s += "set title 'Potential Fields'\n"
		return s

	def draw_line(self, p1, p2):
		'''Return a string to tell Gnuplot to draw a line from point p1 to
		point p2 in the form of a set command.'''
		x1, y1 = p1
		x2, y2 = p2
		return 'set arrow from %s, %s to %s, %s nohead lt 3\n' % (x1, y1, x2, y2)

	def draw_obstacles(self, obstacles):
		'''Return a string which tells Gnuplot to draw all of the obstacles.'''
		s = 'unset arrow\n'
	
		for obs in obstacles:
			last_point = obs[0]
			for cur_point in obs[1:]:
				s += self.draw_line(last_point, cur_point)
				last_point = cur_point
			s += self.draw_line(last_point, obs[0])
		return s

	def plot_field(self, function):
		'''Return a Gnuplot command to plot a field.'''
		s = "plot '-' with vectors head\n"
	
		separation = self.WORLDSIZE / self.SAMPLES
		end = self.WORLDSIZE / 2 - separation / 2
		start = -end

		points = ((x, y) for x in linspace(start, end, self.SAMPLES)
					for y in linspace(start, end, self.SAMPLES))
	
		for x, y in points:
			f_x, f_y = function(x, y)
			plotvalues = self.gpi_point(x, y, f_x, f_y)
			if plotvalues is not None:
				x1, y1, x2, y2 = plotvalues
				s += '%s %s %s %s\n' % (x1, y1, x2, y2)
		s += 'e\n'
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

	# Run the agent
	try:
		while True:
			time_diff = time.time() - prev_time
			agent.tick(time_diff)
	except KeyboardInterrupt:
		print "Exiting due to keyboard interrupt."
		bzrc.close()


if __name__ == '__main__':
	main()

# vim: et sw=4 sts=4
