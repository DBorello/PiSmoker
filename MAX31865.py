import spidev
import time, math, logging, logging.config

#Start logging
logging.config.fileConfig('/home/pi/PiSmoker/logging.conf')
logger = logging.getLogger(__name__)

#Datasheet https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf
class MAX31865:

	def __init__(self,cs,R_0,R_ref,ThreeWire):
		
		self.cs = cs
		self.ThreeWire = ThreeWire
	
		#RTD Constants
		self.R_0 = R_0
		self.R_ref = R_ref
		self.A = 3.90830e-3
		self.B = -5.775e-7
		
		#Setup SPI
		self.spi = spidev.SpiDev()
		self.spi.open(0,cs)
		self.spi.max_speed_hz = 7629 
		self.spi.mode = 0b01
		
		self.config()
	
	def config(self):
		#Config
		# V_Bias (1=on)
		# Conversion Mode (1 = Auto)
		# 1-Shot 
		# 3-Wire (0 = Off)
		# Fault Detection (2 Bits)
		# Fault Detection
		# Fault Status
		# 50/60Hz (0 = 60 Hz)
		if ThreeWire:
			config = 0b11010010 # 0xC2
		else:
			config = 0b11000010 # 0xC2

		self.spi.xfer2([0x80,0xC2])
		time.sleep(0.25)
		self.read()
	
	def read(self):
		MSB = self.spi.xfer2([0x01,0x00])[1]
		LSB = self.spi.xfer2([0x02,0x00])[1]
		
		#Check fault
		if LSB & 0b00000001:
			logger.debug('Fault Detected SPI %i',self.cs)
			self.GetFault()
		
		ADC = ((MSB<<8) + LSB) >> 1 #Shift MSB up 8 bits, add to LSB, remove fault bit (last bit)
		R_T = float(ADC * self.R_ref)/(2**15)
		#print R_T
		try:
			T = self.Resistance2Temp(R_T)
		except:
			T = 0
		return T
		
	def Resistance2Temp(self, R_T):
		R_0 = self.R_0
		A = self.A
		B = self.B
		
		Tc = (-A + math.sqrt(A*A - 4*B*(1-R_T/R_0)))/(2*B)
		Tf = Tc*9/5 + 32	
		return Tf
			
	def GetFault(self):
		Fault = self.spi.xfer2([0x07,0x00])[1]

		if Fault & 0b10000000:
			logger.debug('Fault SPI %i: RTD High Threshold',self.cs)
		if Fault & 0b01000000:
			logger.debug('Fault SPI %i: RTD Low Threshold',self.cs)
		if Fault & 0b00100000:
			logger.debug('Fault SPI %i: REFIN- > 0.85 x V_BIAS',self.cs)
		if Fault & 0b0001000:
			logger.debug('Fault SPI %i: REFIN- < 0.85 x V_BIAS (FORCE- Open)',self.cs)
		if Fault & 0b00001000:
			logger.debug('Fault SPI %i: RTDIN- < 0.85 x V_BIAS (FORCE- Open)',self.cs)
		if Fault & 0b00000100:
			logger.debug('Fault SPI %i: Overvoltage/undervoltage fault',self.cs)
			
	def close(self):
		self.spi.close()