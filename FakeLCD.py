import curses

class LCD.Adafruit_CharLCDPlate():
	def __init__(self):
		self.screen = curses.initscr()

	def message(self,text):
		screen.addstr(5, 5, text)
		screen.refresh()
		
	def home(self):
		pass