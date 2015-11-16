import LCDDisplay, time, Queue

Parameters = {'mode': 'Off', 'target':225, 'P': .01, 'I': 0, 'D': 3.0, 'AugerOnTime': 15, 'AugerOffTime': 65}
Temps = [[1, 2, 3],[4,5,6]]; 

#Initialize LCD
qP = Queue.Queue()
qT = Queue.Queue()
qR = Queue.Queue()

qP.put(Parameters)
qT.put(Temps)

lcd = LCDDisplay.LCDDisplay(qP,qT,qR)
lcd.setDaemon(True)
lcd.start()

i = 1
while True:
	qT.put([[i,i,i],[i,i,i]])

	while not qR.empty():
		NewParameters = qR.get()
		for k in NewParameters:
			Parameters[k] = NewParameters[k]
		qP.put(Parameters)
	i += 1
	time.sleep(0.25)