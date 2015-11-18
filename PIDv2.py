import time
import logging
import logging.config

# Start logging
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

#PID controller based on proportional band

class PID:
	def __init__(self,  PB, Ki, Kd, I_max):
		self.PB = PB #Proportional Band (F)

		self.Ki = Ki
		self.Kd = Kd

		self.P = 0.0
		self.I = 0.0
		self.D = 0.0
		self.PID = 0

		self.Derv = 0.0
		self.Inter = 0.0
		self.Inter_max = I_max

		self.setTarget(0.0)

	def update(self, Current):
		#P
		error = Current - self.setPoint
		self.P = -error*1/self.PB + 0.5 #P = 1 for PB/2 under setPoint, P = 0 for PB/2 over setPoint

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

		logger.info('Target: %d Current: %d Gains: (%f,%f,%f) Errors(%f,%f,%f) Adjustments: (%f,%f,%f) PID: %f' ,self.setPoint, Current,self.PB,self.Ki,self.Kd,error,self.Inter,self.Derv,self.P,self.I,self.D,self.PID)

		return self.PID

	def	setTarget(self, setPoint):
		self.setPoint = setPoint
		self.error = 0.0
		self.Inter = 0.0
		self.Derv = 0.0
		self.LastUpdate = time.time()

	def setGains(self, Kp, Ki, Kd):
		self.Kp = Kp
		self.Ki = Ki
		self.Kd = Kd
		logger.info('New Gains (%f,%f,%f)', Kp, Ki, Kd)

	def getK(self):
		return self.Kp, self.Ki, self.Kd
