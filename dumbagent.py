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
        self.shoottimecounter = 0.0
        self.turntimecounter = 0.0
        self.startangle = 0.0
        self.angleset = False
        

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
        
        # go straight for 5s
        if self.turntimecounter < 5.0:
			for tank in mytanks:
				command = Command(tank.index, 1.0, 0, False)
				self.commands.append(command)
			#self.turntimecounter = 0
		# then turn 90d
        else:
			print "turning"
			tank = mytanks[0]
			if  not self.angleset:
				print "setting new angle"
				self.startangle = tank.angle
				self.angleset = True
			if self.normalize_angle(tank.angle) <= self.normalize_angle(self.startangle + (math.pi / 3)):
				command = Command(tank.index, 1, math.pi, False)
				self.commands.append(command)
			else:
				print "stop turning!!"
				self.angleset = False
				self.turntimecounter = 0	
         
        
        # turn 60degrees every 3s
        #if self.turntimecounter > 3.0:
			
			#for tank in mytanks:
				#command = Command(tank.index, 0, 0.9, False)
				#self.commands.append(command)
			#self.turntimecounter = 0
        
        # shoot every 2s
        if self.shoottimecounter > 2.0:
			print "firing!"
			for tank in mytanks:
				command = Command(tank.index, 0, 0, True)
				self.commands.append(command)
			self.shoottimecounter = 0

        results = self.bzrc.do_commands(self.commands)

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
            #timeA = time.time()
            #print timeA
            time_diff = time.time() - prev_time
            prev_time += time_diff
            
            #print prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
