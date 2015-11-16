import threading, time
import Adafruit_CharLCD as LCD

buttons = ( (LCD.SELECT, 'Mode'),
            (LCD.LEFT,   'Left'  ),
            (LCD.UP,     'Up'    ),
            (LCD.DOWN,   'Down'  ),
            (LCD.RIGHT,  'Right' ))
			
Modes = ('Off','Shutdown','Smoke','Hold')

class LCDDisplay(threading.Thread):
	def __init__(self):
		self.lcd = LCD.Adafruit_CharLCDPlate()
	
	def run(self):
		while True:
			self.UpdateDisplay()
			self.GetButtons()
			time.sleep(0.1)
			
	def UpdateDisplay(self):
		text = '%i/%i/%i\n' % (Parameters['target'],Temps[1],Temps[2])
		text += 'Mode: %s' % (Parameters['mode'])
		
		self.lcd.clear()
		self.lcd.message(text)
		
	def GetButtons(self):
		for button in buttons:
			if self.lcd.is_pressed(button[0])
				if button[1] == 'Mode':
					NewMode =  self.GetCurrentMode() + 1
					if NewMode == len(NewMode):
						NewMode = 0
					NewParameters = {'mode': Modes[NewMode]}
					Parameters = UpdateParameters(NewParameters,Parameters,Temps)
					
				elif button[1] == 'Up':
					NewParameters = {'target': Parameters['target'] + 5}
					Parameters = UpdateParameters(NewParameters,Parameters,Temps)
				elif button[1] == 'Down':
					NewParameters = {'target': Parameters['target'] - 5}
					Parameters = UpdateParameters(NewParameters,Parameters,Temps)	
					
				time.sleep(0.1)
					
				
					
	def GetCurrentMode(self):	
		for i in range(len(Modes)):
			if Parameters['mode'] == Modes[i]:
				return i