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

class Agent(object):
	"""Class handles all command and control logic for a teams tanks."""

	def __init__(self, bzrc):
		self.bzrc = bzrc
		self.constants = self.bzrc.get_constants()
		self.commands = []
		
		self.OBS_TOLERANCE = 10.0
		self.AVOID = 10.0
		
		self.current_target_x = 0.0
		self.current_target_y = 0.0

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
			self.avoid_obstacles(tank)
			
			if tank.flag == '-':
				self.goto_flags(tank)
			else:
				base_x, base_y = self.get_base_center(self.get_my_base())
				tank.add_to_fields(base_x, base_y)
				self.move_to_position(tank)

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
		best_flag = None
		best_dist = 2 * float(self.constants['worldsize'])
		for flag in self.flags:
			dist = math.sqrt((flag.x - tank.x)**2 + (flag.y - tank.y)**2)
			if dist < best_dist:
				best_dist = dist
				best_flag = flag
		if best_flag is None:
			command = Command(tank.index, 0, 0, False)
			self.commands.append(command)
		else:
			tank.add_to_fields(best_flag.x, best_flag.y)
			self.move_to_position(tank)

	def avoid_obstacles(self, tank):
		for obs in self.obstacles:
			last_point = obs[0]
			for cur_point in obs[1:]:
				self.add_repel_field(tank, last_point, cur_point)
				last_point = cur_point	
			self.add_repel_field(tank, last_point, obs[0])

	
	def add_repel_field(self, tank, p1, p2):
		my_x = tank.x
		my_y = tank.y
		
		x1, y1 = p1
		x2, y2 = p2
		if x1 == x2:
			self.add_horizontal_field(p1, p2, tank)
		elif y1 == y2:
			self.add_vertical_field(p1, p2, tank)

	def add_horizontal_field(self, p1, p2, tank):
		x1, y1 = p1
		x2, y2 = p2
		my_x = tank.x
		my_y = tank.y
		
		if my_x >= min([x1, x2]) and my_x <= max([x1, x2]):
			if my_y >= y1 and my_y <= y1 + self.OBS_TOLERANCE:
				tank.add_to_fields(0, self.AVOID)
			elif my_y <= y1 and my_y >= y1 + self.OBS_TOLERANCE:
				tank.add_to_fields(0, -self.AVOID)

	def add_vertical_field(self, p1, p2, tank):
		x1, y1 = p1
		x2, y2 = p2
		my_x = tank.x
		my_y = tank.y
		
		if my_y >= min([y1, y2]) and my_y <= max([y1, y2]):
			if my_x >= x1 and my_x <= x1 + self.OBS_TOLERANCE:
				tank.add_to_fields(self.AVOID, 0)
			elif my_x <= x1 and my_x >= x1 + self.OBS_TOLERANCE:
				tank.add_to_fields(-self.AVOID, 0)


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
			tank.add_to_fields(best_enemy.x, best_enemy.y)
			self.move_to_position(tank)

	def move_to_position(self, tank):
		"""Set command to move to given coordinates."""
		target_x = tank.target_x
		target_y = tank.target_y
		
		target_angle = math.atan2(target_y - tank.y,
								  target_x - tank.x)
		relative_angle = self.normalize_angle(target_angle - tank.angle)
		command = Command(tank.index, 1, 2 * relative_angle, True)
		self.commands.append(command)

	def normalize_angle(self, angle):
		"""Make any angle be between +/- pi."""
		angle -= 2 * math.pi * int (angle / (2 * math.pi))
		if angle <= -math.pi:
			angle += 2 * math.pi
		elif angle > math.pi:
			angle -= 2 * math.pi
		return angle


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
