import math

class PotentialField(object):

    def calculateField(self, x, y):
        raise NotImplemented("not implemented")

class GoalField(PotentialField):
    '''
        GoalField (attraction field), useful for getting Flags and returning Flags
    '''

    def __init__(self, goalX, goalY):
        self.x = goalX
        self.y = goalY
        self.alpha = -10.0       #negative pull's in

    def setGoal(self, x, y):
        '''
        Sets new goal (flag) coordinate
        '''
        self.x = x
        self.y = y

    def calculateField(self, x, y):
        diffX = x - self.x
        diffY = y - self.y
        if diffX == 0 and diffY == 0: #sitting on the goal
            return (0, 0)

        dist = math.sqrt(math.pow(diffX, 2) + math.pow(diffY, 2))
        theta = math.atan2(diffY, diffX)

        retX = self.alpha * math.cos(theta)
        retY = self.alpha * math.sin(theta)

        return (retX, retY)

class RepulsionField(PotentialField):
    '''
        GoalField (attraction field), useful for getting Flags and returning Flags
    '''

    def __init__(self, avoidX, avoidY):
        self.x = avoidX
        self.y = avoidY
        self.alpha = 15
        self.range = 25

    def setAvoid(self, x, y):
        '''
        Sets new goal (flag) coordinate
        '''
        self.x = x
        self.y = y

    def calculateField(self, x, y):
        diffX = x - self.x
        diffY = y - self.y

        if diffX == 0 and diffY == 0:
            return (0, 0)

        dist = math.sqrt(math.pow(diffX, 2) + math.pow(diffY, 2))

        if dist < self.range:
            s = 1.0

            if dist < self.range / 4:
                s = 2.0
            elif dist < self.range / 2:
                s = 1.5

            theta = math.atan2(diffY, diffX)

            retX = self.alpha * s * math.cos(theta)
            retY = self.alpha * s * math.sin(theta)

            return (retX, retY)
        return (0, 0)

class TangentField(PotentialField):

    def __init__(self, cx, cy, r):
        self.x = cx
        self.y = cy
        self.range = r
        self.alpha = -20.0
        self.rotation = +90.0

    def calculateField(self, x, y):
        diffX = x - self.x
        diffY = y - self.y

        dist = math.sqrt(math.pow(diffX, 2) + math.pow(diffY, 2))

        if dist < self.range:
            theta = math.atan2(diffY, diffX)

            retX = self.alpha * math.cos(theta + self.rotation)
            retY = self.alpha * math.sin(theta + self.rotation)

            return (retX, retY)
        return (0, 0)

#Specific fields

class ObstacleField(TangentField):

    def __init__(self, points):
        self.alpha = -20.0
        self.rotation = +90.0
        self.x = 0  #center x
        self.y = 0  #center y
        self.range = 0 #range
        for point in points:
            px, py = point
            self.x += float(px)
            self.y += float(py)

        self.x = self.x / float(len(points))
        self.y = self.y / float(len(points))

        for point in points:
            px, py = point
            px = float(px)
            py = float(py)
            dist = math.sqrt(math.pow(self.x - px, 2) + math.pow(self.y - py, 2))
            if dist > self.range:
                self.range = dist * 1.25

class ShotField(RepulsionField):

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alpha = 15.0
        self.range = 50.0

class TankField(RepulsionField):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alpha = 15
        self.range = 10
