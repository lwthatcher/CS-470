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
		self.OBS_TOLERANCE = 30.0
		self.S = 50
		self.wroteonce = False
		self.goalradius = 30

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
		
		make_map = GnuPlot(self, self.flags, self.obstacles) 
		
		if not self.wroteonce:
			make_map.generateGnuMap()
			self.wroteonce = True
		
		for tank in mytanks:
			if tank.flag == '-':
				self.goto_flags(tank)
			else:
				base_x, base_y = self.get_base_center(self.get_my_base())
				self.move_to_position(tank, base_x, base_y)

		results = self.bzrc.do_commands(self.commands)


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

	def attack_enemies(self, tank):
		"""Find the closest enemy and chase it, shooting as you go."""
		best_enemy = None
		best_dist = 2 * float(self.constants['worldsize'])
		for enemy in self.enemies:
			if enemy.status != 'alive':
				continue
			dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
			if dist < best_dist:
				best_dist = dist
				best_enemy = enemy
		if best_enemy is None:
			command = Command(tank.index, 0, 0, False)
			self.commands.append(command)
		else:
			self.move_to_position(tank, best_enemy.x, best_enemy.y)

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

	def move_to_position(self, tank, target_x, target_y):
		"""Set command to move to given coordinates."""
		
		#get deltas
		delta_xG, delta_yG, magnitude = self.calculate_objective_delta(tank.x, tank.y, target_x, target_y)
		delta_xO, delta_yO = self.calculate_obstacles_delta(tank.x, tank.y)
		
		#combine
		delta_x = delta_xG + delta_xO
		delta_y = delta_yG + delta_yO
		
		#calculate angle
		turn_angle = math.atan2(delta_y, delta_x)
		relative_angle = self.normalize_angle(turn_angle - tank.angle)
		
		#put lower bound on speed: no slower than 40%
		if magnitude < 0.4:
			magnitude = 0.4
		
		command = Command(tank.index, magnitude, 2 * relative_angle, True)
		self.commands.append(command)
	
	def get_obstacle_force(self, obstacle, x, y):
		# I need to go around the obstacle and calculate the min_x and min_y distance for the tank
		
		delta_x = 0 
		delta_y = 0
		
		p1 = obstacle[0]
		for p2 in obstacle[1:]:
			repel_x, repel_y = self.get_repel_field(x, y, p1, p2)
			delta_x += repel_x
			delta_y += repel_y				
			p1 = p2
		
		repel_x, repel_y = self.get_repel_field(x, y, p2, obstacle[0])
				
		return delta_x, delta_y
	
	def get_repel_field(self, x, y, p1, p2):
		my_x = x
		my_y = y
		
		if self.between_endpoints(my_x, my_y, p1, p2): # need to consider if it's between the start and end of the line
			x1, y1 = p1
			x2, y2 = p2
			
			# find the distance from the tank to the line formed by p1 and p2
			# ax + by + c = 0
			a = y1 - y2
			b = x2 - x1
			c = x1 * y2 - x2 * y1
			
			sqnorm = math.sqrt(a**2 + b**2)
			
			# shortest distance from tank to obstacle
			dist = abs(a * my_x + b * my_y + c) / sqnorm
			
			if dist < self.OBS_TOLERANCE:
				# normal vector purpendicular to the obstacle
				n_hat = [a / sqnorm, b / sqnorm] 
				
				# get the point on the obstacle that is closest to the tank
				scalar = dist - self.dot(my_x, my_y, n_hat)
				#scalar = self.dot(my_x, my_y, n_hat) - dist
				
				obs_point = [my_x + scalar * n_hat[0], my_y + scalar * n_hat[1]]
				
				'''print "obs_point: ", obs_point
				print "tank.x: ", my_x
				print "tank.y: ", my_y
				print "dist: ", dist
				print "scalar: ", scalar
				print'''
				
				# angle between the tank and the obstacle
				theta = self.get_theta(my_x, my_y, p1, p2, obs_point[0], obs_point[1])

				delta_x = -self.BETA * (self.OBS_TOLERANCE - dist) * math.cos(theta) # math.cos returns in radians
				delta_y = -self.BETA * (self.OBS_TOLERANCE - dist) * math.sin(theta)
				
				return delta_x, delta_y
			else:
				return 0, 0
		else:
			return 0, 0 # this obstacle doesn't have a repelling affect on the tank
	
	def get_theta(self, x, y, p1, p2, obs_x, obs_y):
		x1, y1 = p1
		x2, y2 = p2
		
		'''print "x: ", x
		print "y: ", y
		print "obs_x: ", obs_x
		print "obs_y: ", obs_y'''
		
		theta = 0
		
		if self.is_vertical(x1, x2):
			if x < obs_x: #the tank is on the left side of the obstacle
				theta = math.atan2(obs_y - y, obs_x - x)
				#print "vertical left theta: ", theta
			else: # the tank is on the right side of the obstacle
				theta = math.atan2(obs_y - y, obs_x - x)
				#print "vertical right theta: ", theta
		
		elif self.is_horizontal(y1, y2):
			#print "obs_y: ", obs_y
			if y <= obs_y: # the tank is north of the line
				if y < 0:
					theta = math.atan2(y - obs_y, obs_x - x)
				else:
					theta = math.atan2(y - obs_y, obs_x - x)
				#print "horizontal north theta: ", theta
			else: # the tank is south of the line
				if y < 0:
					theta = math.atan2(y - obs_y, x - obs_x)
				else:
					theta = math.atan2(obs_y - y, x - obs_x)
				#print "horizontal south theta: ", theta
		
		return theta
	
	def is_horizontal(self, y1, y2):
		if y1 == y2:
			return True
		else:
			return False
			
	def is_vertical(self, x1, x2):
		if x1 == x2:
			return True
		else:
			return False
	
	def between_endpoints(self, x, y, p1, p2):
		x1, y1 = p1
		x2, y2 = p2
		
		if self.is_vertical(x1, x2): # vertical line
			if y > min([y1, y2]) and y < max([y1, y2]):
				return True
			else:
				return False
		elif self.is_horizontal(y1, y2): # horizontal line
			if x > min([x1, x2]) and x < max([x1,x2]):
				return True
			else:
				return False
		else: # diagonal line (this checks a box)
			if x > min([x1, x2]) and x < max([x1, x2]) and y > min([y1, y2]) and y < max([y1, y2]):
				return True
			else:
				return False
	
	def dot(self, x, y, n_hat):
		return (x * n_hat[0] + y * n_hat[1])
	
	def normalize_angle(self, angle):
		"""Make any angle be between +/- pi."""
		angle -= 2 * math.pi * int (angle / (2 * math.pi))
		if angle <= -math.pi:
			angle += 2 * math.pi
		elif angle > math.pi:
			angle -= 2 * math.pi
		return angle

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
		
		def function(x, y):
			target = self.agent.get_best_flag(x, y)
			
			#get deltas
			delta_xG, delta_yG = [0, 0]
			magnitude = 1
			##delta_xG, delta_yG, magnitude = self.agent.calculate_objective_delta(x, y, target.x, target.y)
			delta_xO, delta_yO = self.agent.calculate_obstacles_delta(x, y)
			
			#combine
			delta_x = delta_xG + delta_xO
			delta_y = delta_yG + delta_yO
			
			#put lower bound on speed limit
			if magnitude < 0.4:
				magnitude = 0.4
			
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
