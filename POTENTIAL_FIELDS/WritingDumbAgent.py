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
        self.shoottimecounter = 0.0
        self.turntimecounter = 0.0
        self.startangle = 0.0
        self.angleset = False
        self.turnangle = math.pi / 3
        self.writeonce = True
        
        # Output file:
        self.FILENAME = 'testfields.gpi'
        # Size of the world (one of the "constants" in bzflag):
        self.WORLDSIZE = 800
        # How many samples to take along each dimension:
        self.SAMPLES = 25
        # Change spacing by changing the relative length of the vectors.  It looks
        # like scaling by 0.75 is pretty good, but this is adjustable:
        self.VEC_LEN = 0.75 * self.WORLDSIZE / self.SAMPLES
			
        

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []
        
        self.shoottimecounter += time_diff
        self.turntimecounter += time_diff
        
        
        
        if self.turntimecounter >= 10.0:
			#print "turning"
			if  not self.angleset:
				#print "setting new angle"
				self.startangle = mytanks[0].angle
				#print "startangle: ", self.startangle
				self.angleset = True
				self.turntimecounter = 0
				if self.writeonce:
					print "writing to file!"
					self.generateGnuMap()
					self.writeonce = False
				
		

        if self.angleset == True:
			endangle = self.startangle + self.turnangle
			if self.turnangle > 0: # turning left
				if self.startangle >= 0:
					if self.normalize_angle(endangle) > 0: # the sign stayes the same
						if self.normalize_angle(mytanks[0].angle) <= self.normalize_angle(endangle):
							command = Command(mytanks[0].index, 0, math.pi, False)
							self.commands.append(command)
						else:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
					else: # the sign changes
						if self.normalize_angle(mytanks[0].angle) > self.normalize_angle(endangle) and self.normalize_angle(mytanks[0].angle) < 0:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
						else:
							command = Command(mytanks[0].index, 0, math.pi, False)
							self.commands.append(command)
				else: # self.startangle < 0
					if self.normalize_angle(endangle) < 0: # the sign stays the same
						if self.normalize_angle(mytanks[0].angle) <= self.normalize_angle(endangle):
							command = Command(mytanks[0].index, 0, math.pi, False)
							self.commands.append(command)
						else:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
					else: # the sign changes
						if self.normalize_angle(mytanks[0].angle) > self.normalize_angle(endangle) and self.normalize_angle(mytanks[0].angle) > 0:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
						else:
							command = Command(mytanks[0].index, 0, math.pi, False)
							self.commands.append(command)
			else: #turning right
				if self.startangle >= 0:
					if self.normalize_angle(endangle) > 0: # the sign stayes the same
						if self.normalize_angle(mytanks[0].angle) >= self.normalize_angle(endangle):
							command = Command(mytanks[0].index, 0, -math.pi, False)
							self.commands.append(command)
						else:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
					else: # the sign changes
						if self.normalize_angle(mytanks[0].angle) < self.normalize_angle(endangle) and self.normalize_angle(mytanks[0].angle) < 0:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
						else:
							command = Command(mytanks[0].index, 0, -math.pi, False)
							self.commands.append(command)
				else: # self.startangle < 0
					if self.normalize_angle(endangle) < 0: # the sign stays the same
						if self.normalize_angle(mytanks[0].angle) >= self.normalize_angle(endangle):
							command = Command(mytanks[0].index, 0, -math.pi, False)
							self.commands.append(command)
						else:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
					else: # the sign changes
						if self.normalize_angle(mytanks[0].angle) < self.normalize_angle(endangle) and self.normalize_angle(mytanks[0].angle) > 0:
							self.angleset = False
							command = Command(mytanks[0].index, 1.0, 0, False)
						else:
							command = Command(mytanks[0].index, 0, -math.pi, False)
							self.commands.append(command)
						
				
				
				
				
				
			#if self.normalize_angle(mytanks[0].angle) >= self.normalize_angle(self.startangle + (math.pi / 3)):
				#print "normalize_angle"
				#command = Command(mytanks[0].index, 0, math.pi, False)
				#self.commands.append(command)
			#else:
				#print "stop turning!!"
				#self.angleset = False
				#command = Command(mytanks[0].index, 1.0, 0, False)
        else:
			command = Command(mytanks[0].index, 1.0, 0, False)
			self.commands.append(command)
			
			#self.turntimecounter = 0
         
        
        
        # shoot every 2s
        if self.shoottimecounter > 2.0:
			print "firing!"
			command = Command(mytanks[0].index, 0, 0, True)
			self.commands.append(command)
			self.shoottimecounter = 0

        results = self.bzrc.do_commands(self.commands)
	
    def turning(self, tankangle, tankindex):
		command = Command(tankindex, 1, math.pi, False)
		self.commands.append(command)
		
    def generateGnuMap(self):
    	outfile = open(self.FILENAME, 'w')
    	minimum = -self.WORLDSIZE / 2
    	maximum = self.WORLDSIZE / 2
    	print >>outfile, self.gnuplot_header(minimum, maximum)
    	print >>outfile, self.draw_obstacles(self.bzrc.get_obstacles())
    	field_function = self.generate_field_function(150)
    	print >>outfile, self.plot_field(field_function)
    	outfile.close()

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

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
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
        
	########################################################################
	# Field and Obstacle Definitions

    def generate_field_function(self, scale):
    	def function(x, y):
    		'''User-defined field function.'''
    		sqnorm = (x + y**2)
    		if sqnorm == 0.0:
    			return 0, 0
    		else:
    			return x*scale/sqnorm, y*scale/sqnorm
    	return function
    
    #OBSTACLES = [((0, 0), (-150, 0), (-150, -50), (0, -50)),
    #				((200, 100), (200, 330), (300, 330), (300, 100))]
    
    #OBSTACLES = self.bzrc.get_obstacles()
    
    
    ########################################################################
    # Helper Functions
    
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
            prev_time += time_diff
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
