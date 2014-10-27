#!/usr/bin/env python

##OpenGL.ERROR_CHECKING = False
#from OpenGL.GL import *
#from OpenGL.GLUT import *
#from OpenGL.GLU import *
#from numpy import zeros

class Bayes:
	

	def __init__(self):
		self.OBS_GIVEN_OCC = 0.97
		self.NOT_OBS_GIVEN_NOT_OCC = 0.9
		self.NOT_OBS_GIVEN_OCC = 0.03
		self.OBS_GIVEN_NOT_OCC = 0.1
		
	def set_obs_given_occ(self, prob):
		self.OBS_GIVEN_OCC = prob
		
	def self_not_obs_given_not_occ(self, prob):
		self.NOT_OBS_GIVEN_NOT_OCC = prob
		
	def probability_occupied_given_observed(self, prior):
		numerator = self.OBS_GIVEN_OCC * prior
		denominator = self.prob_obs(prior)
		answer = numerator / denominator
		return answer

	def probability_occupied_given_not_observed(self, prior):
		numerator = self.prob_occ_and_not_obs(prior)
		denominator = self.prob_not_obs(prior)
		answer = numerator / denominator
		return answer

	def prob_not_obs(self, prior):
		return (1 - self.prob_obs(prior))

	def prob_obs(self, prior):
		answer = self.prob_occ_and_obs(prior) + self.prob_not_occ_and_obs(prior)
		return answer
		
	def prob_occ_and_not_obs(self, prior):
		answer = self.NOT_OBS_GIVEN_OCC * prior
		return answer

	def prob_occ_and_obs(self, prior):
		answer = self.OBS_GIVEN_OCC * prior
		return answer
	
	def prob_not_occ_and_obs(self, prior):
		not_occ = (1.0 - prior)
		answer = self.OBS_GIVEN_NOT_OCC * not_occ
		return answer

