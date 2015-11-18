import threading, time
import Adafruit_CharLCD as LCD
#import FakeLCD as LCD

buttons = ( (LCD.SELECT, 'Mode'),
            (LCD.LEFT,   'Left'  ),
            (LCD.UP,     'Up'    ),
            (LCD.DOWN,   'Down'  ),
            (LCD.RIGHT,  'Right' ))
			
Modes = ('Off','Shutdown','Smoke','Hold')

class LCDDisplay(threading.Thread):
	def __init__(self,qP,qT,qR):
		threading.Thread.__init__(self)
		self.lcd = LCD.Adafruit_CharLCDPlate()
		
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
		text = '%i/%i/%i\n' % (self.Parameters['target'],self.Ts[1],self.Ts[2])
		text += 'Mode: %s' % (self.Parameters['mode'].ljust(10))

		self.lcd.home()
		self.lcd.message(text)
		
	def GetButtons(self):
		for button in buttons:
			if self.lcd.is_pressed(button[0]):
				if button[1] == 'Mode':
					NewMode =  self.GetCurrentMode() + 1
					if NewMode == len(Modes):
						NewMode = 0
					NewParameters = {'mode': Modes[NewMode]}
					print NewParameters
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
