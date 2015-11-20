import threading
import time
import logging
import logging.config

#import FakeLCD as LCD

buttons = ( (LCD.SELECT, 'Mode'),
            (LCD.LEFT,   'Left'  ),
            (LCD.UP,     'Down'    ), #Hardware snafu 
            (LCD.DOWN,   'Up'  ),
            (LCD.RIGHT,  'Right' ))
			
Modes = ('Off','Shutdown','Smoke','Hold')

# Start logging
logging.config.fileConfig('/home/pi/PiSmoker/logging.conf')
logger = logging.getLogger(__name__)

class LCDDisplay(threading.Thread):
	def __init__(self, qP, qT, qR):
		threading.Thread.__init__(self)
		try:
			self.lcd = LCD.Adafruit_CharLCDPlate()
		except:
			logger.info('Unable to initialize LCD')
		
		self.qP = qP
		self.qT = qT
		self.qR = qR


	def run(self):
		while True:
			self.GetButtons()
			while not self.qP.empty():
				self.Parameters = self.qP.get()
			while not self.qT.empty():
				self.Ts = self.qT.get()

			self.UpdateDisplay()
			time.sleep(0.01)
			
	def UpdateDisplay(self):
		text = 'T%i G%i M%i\n' % (self.Parameters['target'],self.Ts[1],self.Ts[2])

		if self.Parameters['mode'] == 'Hold' or self.Parameters['mode'] == 'Smoke':
			text += '%s %3.2f   %s' % (self.Parameters['mode'].ljust(5),self.Parameters['u'],self.GetCurrentState())
		else:
			text += '%s' % (self.Parameters['mode'].ljust(16))

		try:
			self.lcd.home()
			self.lcd.message(text)
		except:
			logger.info('Unable to update LCD - %s',text)


	def GetButtons(self):
		for button in buttons:
			if self.lcd.is_pressed(button[0]):
				if button[1] == 'Mode':
					NewMode =  self.GetCurrentMode() + 1
					if NewMode == len(Modes):
						NewMode = 0
					NewParameters = {'mode': Modes[NewMode]}
					self.qR.put(NewParameters)
				elif button[1] == 'Up':
					NewParameters = {'target': self.Parameters['target'] + 5}
					self.qR.put(NewParameters)
				elif button[1] == 'Down':
					NewParameters = {'target': self.Parameters['target'] - 5}
					self.qR.put(NewParameters)
		
	def GetCurrentMode(self):	
		for i in range(len(Modes)):
			if self.Parameters['mode'] == Modes[i]:
				return i

	def GetCurrentState(self):
		State = ''
		if self.Parameters['fan']:
			State += 'F'
		else:
			State += ' '
		
		if self.Parameters['igniter']:
			State += 'I'
		else:
			State += ' '
			
		if self.Parameters['auger']:
			State += 'A'
		else:
			State += ' '
			
		return State