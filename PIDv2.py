import time
import logging
import logging.config

# Start logging
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

#PID controller based on proportional band in standard PID form https://en.wikipedia.org/wiki/PID_controller#Ideal_versus_standard_PID_form
# u = Kp (e(t)+ 1/Ti INT + Td de/dt)
# PB = Proportional Band
# Ti = Goal of eliminating in Ti seconds
# Td = Predicts error value at Td in seconds

class PID:
	def __init__(self,  PB, Ti, Td, I_max):
		self.CalculateGains(PB,Ti,Td)

		self.P = 0.0
		self.I = 0.0
		self.D = 0.0
		self.PID = 0

		self.Derv = 0.0
		self.Inter = 0.0
		self.Inter_max = I_max

		self.setTarget(0.0)

	def CalculateGains(self,PB,Ti,Td):
		self.Kp = -1/PB
		self.Ki = self.Kp/Ti
		self.Kd = self.Kp*Td

	def update(self, Current):
		#P
		error = Current - self.setPoint
		self.P = self.Kd + 0.5 #P = 1 for PB/2 under setPoint, P = 0 for PB/2 over setPoint

		#I
		dT = time.time() - self.LastUpdate
		if self.P > 0 and self.P < 1: #Ensure we are in the PB, otherwise do not calculate I to avoid windup
			self.Inter += error*dT
			self.Inter = max(self.Inter, -self.Inter_max)
			self.Inter = min(self.Inter, -self.Inter_max)

		self.I = self.Ki * self.Inter

		#D
		self.Derv = (error - self.error)/dT
		self.D = self.Kd * self.Derv

		#PID
		self.PID = self.P + self.I + self.D

		#Update for next cycle
		self.error = error
		self.LastUpdate = time.time()

		logger.info('Target: %d Current: %d Gains: (%f,%f,%f) Errors(%f,%f,%f) Adjustments: (%f,%f,%f) PID: %f' ,self.setPoint, Current,self.Kd,self.Ki,self.Kd,error,self.Inter,self.Derv,self.P,self.I,self.D,self.PID)

		return self.PID

	def	setTarget(self, setPoint):
		self.setPoint = setPoint
		self.error = 0.0
		self.Inter = 0.0
		self.Derv = 0.0
		self.LastUpdate = time.time()

	def setGains(self, PB, Ti, Td):
		self.CalculateGains(PB,Ti,Kd)
		logger.info('New Gains (%f,%f,%f)', self.Kp, self.Ki, self.Kd)

	def getK(self):
		return self.Kp, self.Ki, self.Kd
