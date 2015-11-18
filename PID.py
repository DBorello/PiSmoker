import time
import logging
import logging.config

# Start logging
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)


class PID:
	def __init__(self, Kp, Ki, Kd, I_min, I_max):
		self.Kp = Kp
		self.Ki = Ki
		self.Kd = Kd

		self.P = 0.0
		self.I = 0.0
		self.D = 0.0
		self.PID = 0

		self.Derv = 0.0
		self.Inter = 0.0
		self.Inter_max = I_max
		self.Inter_min = I_min

		self.setTarget(0.0)

	def update(self, Current):
		error = Current - self.setPoint

		dT = time.time() - self.LastUpdate
		self.Inter += error*dT
		self.Inter = min(max(self.Inter, self.Inter_min), self.Inter_max)

		self.Derv = (error - self.error)/dT

		self.P = self.Kp * error
		self.I = self.Ki * self.Inter
		self.D = self.Kd * self.Derv
		self.PID = self.P + self.I + self.D

		self.error = error
		self.LastUpdate = time.time()

		logger.info('Target: %d Current: %d Gains: (%f,%f,%f) P: %f I: %f D: %f Adjustments: (%f,%f,%f) PID: %f' ,self.setPoint, Current,self.Kp,self.Ki,self.Kd,error,self.Inter,self.Derv,self.P,self.I,self.D,self.PID)

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
