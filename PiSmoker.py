import time
import json
import os
import datetime
import logging
import logging.config
import Queue
import numpy as np
import RPi.GPIO as GPIO
import MAX31865
import Traeger
import PID as PID
import LCDDisplay
from firebase import firebase

#Start logging
logging.config.fileConfig('/home/pi/PiSmoker/logging.conf')
logger = logging.getLogger('PiSmoker')

#Start firebase
firebase = firebase.FirebaseApplication('https://pismoker.firebaseio.com/', None)

#Parameters
TempInterval = 3 #Frequency to record temperatures
TempRecord = 60 #Period to record temperatures in memory
ParametersInterval = 1#Frequency to write parameters
PIDCycleTime = 20#Frequency to update control loop
ReadParametersInterval =3  #Frequency to poll web for new parameters
u_min = 0.15 #Maintenance level
u_max = 1.0 #
IgniterTemperature = 100 #Temperature to start igniter
ShutdownTime = 10*60 # Time to run fan after shutdown
Relays = {'auger': 22, 'fan': 18, 'igniter': 16} #Board
Relays = {'auger': 25, 'fan': 24, 'igniter': 23}  #BCM
Parameters = {'mode': 'Off', 'target':225, 'PB': 40, 'Ti': 180, 'Td': 45, 'CycleTime': 20, 'u': 0.15}

#PID controller based on proportional band in standard PID form https://en.wikipedia.org/wiki/PID_controller#Ideal_versus_standard_PID_form
# u = Kp (e(t)+ 1/Ti INT + Td de/dt)
# PB = Proportional Band
# Ti = Goal of eliminating in Ti seconds (Make large to disable integration)
# Td = Predicts error value at Td in seconds


#Initialize RTD Probes
T = []
T.append(MAX31865.MAX31865(1,1000,4000)) #Grill
T.append(MAX31865.MAX31865(0,100,400)) #Meat

#Initialize Traeger Object
G = Traeger.Traeger(Relays)

#Initialize LCD
qP = Queue.Queue() #Queue for Parameters
qT = Queue.Queue() #Queue for Temps
qR = Queue.Queue() #Return for Parameters
qP.put(Parameters)
qT.put([0,0,0])
lcd = LCDDisplay.LCDDisplay(qP, qT, qR)
lcd.setDaemon(True)
lcd.start()

#Start controller
Control = PID.PID(Parameters['PB'],Parameters['Ti'],Parameters['Td'])
Control.setTarget(Parameters['target'])


def RecordTemps(Parameters, Temps):
	if len(Temps) == 0 or time.time() - Temps[-1][0] > TempInterval:
		Ts = [time.time()]
		for t in T:
			Ts.append(t.read())
		Temps.append(Ts)
		PostTemps(Parameters, Ts)
		
		#Clean up old temperatures
		NewTemps = []
		for Ts in Temps:
			if time.time() - Ts[0] < TempRecord: #Still valid
				NewTemps.append(Ts)
				
		#Push temperatures to LCD
		qT.put(Ts)
				
		return NewTemps
				
	return Temps

def PostTemps(Parameters, Ts):
	try:
		r = firebase.post_async('/Temps', {'time': Ts[0]*1000, 'TT': Parameters['target'], 'T1': Ts[1], 'T2':Ts[2]} , params={'print': 'silent'}, callback=PostCallback)
	except:
		logger.info('Error writing Temps to Firebase')


def PostCallback(data=None):
	pass
		
def ResetFirebase(Parameters):
	r = firebase.put('/','Parameters',Parameters, {'print':'silent'})
	r = firebase.delete('/','Temps')
	r = firebase.delete('/','Controls')


def WriteParameters(Parameters):
	'''Write parameters to file'''

	for r in Relays:
		Parameters[r] = G.GetState(r)

	Parameters['LastWritten'] = time.time()
	qP.put(Parameters)
			
	try:
		r = firebase.patch_async('/Parameters', Parameters, params={'print': 'silent'}, callback=PostCallback)
	except:
		logger.info('Error writing parameters to Firebase')
		
	return Parameters


def ReadParameters(Parameters, Temps):
	'''Read parameters file written by web server and LCD'''
	#Read from queue
	while not qR.empty():
		NewParameters = qR.get()
		Parameters = UpdateParameters(NewParameters,Parameters,Temps)
		
	#Read from webserver
	if time.time() - Parameters['LastReadWeb'] > ReadParametersInterval:
		Parameters['LastReadWeb'] = time.time()
		try:
			NewParameters = firebase.get('/Parameters',None )
			Parameters = UpdateParameters(NewParameters,Parameters,Temps)
		except:
			logger.info('Error reading parameters to Firebase')
			return Parameters
		
	return Parameters


def UpdateParameters(NewParameters,Parameters,Temps):
	#Loop through each key, see what changed
	for k in NewParameters.keys():
		if k == 'target':
			if float(Parameters[k]) != float(NewParameters[k]):
				logger.info('New Parameters: %s -- %f (%f)', k,float(NewParameters[k]),Parameters[k])
				Control.setTarget(float(NewParameters[k]))
				Parameters[k] = float(NewParameters[k])
				Parameters = WriteParameters(Parameters)
		elif k == 'P' or k == 'I' or k == 'D':
			if float(Parameters[k]) != float(NewParameters[k]):
				logger.info('New Parameters: %s -- %f (%f)', k,float(NewParameters[k]),Parameters[k])
				Parameters[k] = float(NewParameters[k])
				Control.setGains(Parameters['PB'],Parameters['Ti'],Parameters['Td'])
				Parameters = WriteParameters(Parameters)
		elif k == 'mode':
			if Parameters[k] != NewParameters[k]:
				logger.info('New Parameters: %s -- %s (%s)', k,NewParameters[k],Parameters[k])
				Parameters[k] = NewParameters[k]
				Parameters = SetMode(Parameters, Temps)
				Parameters = WriteParameters(Parameters)

	return Parameters


def GetAverageSince(Temps,startTime):
	n = 0
	sum = [0]*len(Temps[0])
	for Ts in Temps:
		if Ts[0] < startTime:
			continue
		for i in range(0,len(Ts)): #Add
			sum[i] += Ts[i]
		
		n += 1
		
	Avg = np.array(sum)/n
	
	return Avg.tolist()
	
	
#Modes	
def SetMode(Parameters, Temps):
	if Parameters['mode'] == 'Off':
		logger.info('Setting mode to Off')
		G.Initialize()
		
	elif Parameters['mode'] == 'Shutdown':
		G.Initialize()
		G.SetState('fan',True)
		
	elif Parameters['mode'] == 'Smoke':
		G.SetState('fan',True)
		G.SetState('auger',True)
		CheckIgniter(Temps)
		Parameters['CycleTime'] = 80
		Parameters['u'] = 15.0/(15.0+65.0) #P2
		
	elif Parameters['mode'] == 'Hold':
		G.SetState('fan',True)
		G.SetState('auger',True)
		CheckIgniter(Temps)
		Parameters['CycleTime'] = PIDCycleTime
		Parameters['u'] = u_min #Set to maintenance level
		
	WriteParameters(Parameters)	
	return Parameters	


def DoMode(Parameters,Temps):
	if Parameters['mode'] == 'Off':
		pass
	
	elif Parameters['mode'] == 'Shutdown':
		if (time.time() - G.ToggleTime['fan']) > ShutdownTime:
			Parameters['mode'] = 'Off'
			Parameters = SetMode(Parameters, Temps)
		
	elif Parameters['mode'] == 'Smoke':
		DoAugerControl(Parameters,Temps)
		
	elif Parameters['mode'] == 'Hold':
		Parameters = DoControl(Parameters,Temps)
		DoAugerControl(Parameters,Temps)

	return Parameters
		

def DoAugerControl(Parameters,Temps):

	#Auger currently on AND TimeSinceToggle > Auger On Time
	if G.GetState('auger') and (time.time() - G.ToggleTime['auger']) > Parameters['CycleTime']*Parameters['u'] and Parameters['u'] < 1.00:
		G.SetState('auger',False)
		CheckIgniter(Temps)
		WriteParameters(Parameters)
		
	#Auger currently off AND TimeSinceToggle > Auger Off Time
	if (not G.GetState('auger')) and (time.time() - G.ToggleTime['auger']) > Parameters['CycleTime']*(1-Parameters['u']):
		G.SetState('auger',True)
		CheckIgniter(Temps)
		WriteParameters(Parameters)


def CheckIgniter(Temps):
		#Check if igniter needed
		if Temps[-1][1] < IgniterTemperature:
			G.SetState('igniter',True)
		else:
			G.SetState('igniter',False)
	
	
def DoControl(Parameters, Temps):
	if (time.time() - Control.LastUpdate) > Parameters['CycleTime']:

		Avg = GetAverageSince(Temps,Control.LastUpdate)
		Parameters['u'] = Control.update(Avg[1]) #Grill probe is [0] in T, [1] in Temps
		Parameters['u'] = max(Parameters['u'],u_min)
		Parameters['u'] = min(Parameters['u'],u_max)
		logger.info('u %f',Parameters['u'])
		
		#Post control state
		D = {'time': time.time()*1000, 'u': Parameters['u'], 'P': Control.P, 'I': Control.I, 'D': Control.D, 'PID': Control.u, 'Error':Control.error, 'Derv':Control.Derv, 'Inter':Control.Inter}

		try:
			r = firebase.post_async('/Controls', D , params={'print': 'silent'}, callback=PostCallback)
		except:
			logger.info('Error writing Controls to Firebase')

		Parameters = WriteParameters(Parameters)
		
		
	return Parameters

##############
#Setup       #
##############

#Default parameters
Parameters = WriteParameters(Parameters)

#Setup variables
Temps = [] #List, [time, T[0], T[1]...]
ResetFirebase(Parameters)

#Set mode
SetMode(Parameters, Temps)
Parameters['LastReadWeb'] = time.time()

###############
#Main Loop    #
###############
while 1:
	#Record temperatures
	Temps = RecordTemps(Parameters, Temps)
		
	#Check for new parameters
	Parameters = ReadParameters(Parameters, Temps)

	#Do mode
	Parameters = DoMode(Parameters,Temps)
			
	time.sleep(0.05)
