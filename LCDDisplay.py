import threading, time
import Adafruit_CharLCD as LCD

class LCDDisplay(threading.Thread):
	def __init__(self):
		self.lcd = LCD.Adafruit_CharLCDPlate()
	
	def run(self):
		while 1:
			self.UpdateDisplay()
			self.GetButtons()
			time.sleep(0.1)
			
	def UpdateDisplay(self):
		text = '%i/%i/%i\n' % (Parameters['target'],Temps[1],Temps[2])
		text += 'Mode: %s' % (Parameters['mode'])
		
		self.lcd.clear()
		self.lcd.message(text)