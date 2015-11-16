import time, json, os, datetime, logging, logging.config
import numpy as np
import RPi.GPIO as GPIO
import MAX31865
import Traeger
import PID
import LCDDisplay
from firebase import firebase

#Start logging
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('PiSmoker')

#Start firebase
firebase = firebase.FirebaseApplication('https://pismoker.firebaseio.com/', None)

#Parameters
OutputDir = '/home/pi/www/output'
ParametersPath = '/home/pi/www/Parameters.json'
TempInterval = 3 #Frequency to record temperatures
ParametersInterval = 1#Frequency to write parameters
ControlInterval = 60#Frequency to update control loop
ReadParametersInterval =30
AugerOffMax = 90
IgniterTemperature = 100 #Temperature to start igniter
ShutdownTime = 10*60 # Time to run fan after shutdown
Relays = {'auger': 22, 'fan': 18, 'igniter': 16}
Parameters = {'mode': 'Off', 'target':225, 'P': .01, 'I': 0, 'D': 3.0, 'AugerOnTime': 15, 'AugerOffTime': 65}

#Initialize RTD Probes
T = []
T.append(MAX31865.MAX31865(1,1000,4000)) #Grill
T.append(MAX31865.MAX31865(0,100,400)) #Meat


#Create symlinks
BaseName = datetime.datetime.now().strftime('%Y%m%d-%H%M%S_')
os.remove(os.path.join(OutputDir,'Temperatures.json'))
os.symlink(os.path.join(OutputDir,BaseName+'Temperatures.json'),os.path.join(OutputDir,'Temperatures.json'))

#Initialize Traeger Object
G = Traeger.Traeger(Relays)

#Initialize LCD
lcd = LCDDisplay.LCDDisplay()
l.setDaemon(True)
lcd.start()

#Start controller
Control = PID.PID(Parameters['P'],Parameters['I'],Parameters['D'],-500,500)
Control.setTarget(Parameters['target'])


def RecordTemps(Temps):
	if len(Temps) == 0 or time.time() - Temps[-1][0] > TempInterval:
		Ts = [CurrentTime]
		for t in T:
			Ts.append(t.read())
		Temps.append(Ts)
		PostTemps(Ts)
		
		#Clean up old temperatures
		NewTemps = []
		for Ts in Temps:
			if time.time() - Ts[0] < TempRecord: #Still valid
				NewTemps.append(Ts)
				
		return NewTemps
				
	return Temps

def PostTemps(Ts):
	try:
		r = firebase.post_async('/Temps', {'time': Ts[0]*1000, 'T1': Ts[1], 'T2':Ts[2]} , params={'print': 'silent'}, callback=PostCallback)
	except:
		logger.info('Error writing Temps to Firebase')

def PostCallback(data=None):
	None
		
def ResetFirebase(Parameters):
	r = firebase.put('/','Parameters',Parameters, {'print':'silent'})
	r = firebase.delete('/','Temps')
	r = firebase.delete('/','Controls')
	
def WriteParameters(Parameters):
	'''Write parameters to file'''
	Parameters['LastWritten'] = time.time()
	
	for r in Relays:
		Parameters[r] = G.GetState(r)

	try:
		r = firebase.patch_async('/Parameters', Parameters, params={'print': 'silent'}, callback=PostCallback)
	except:
		logger.info('Error writing parameters to Firebase')
		
	return Parameters
	
def ReadParameters(Parameters, Temps):
	'''Read parameters file written by web server'''
	try:
		NewParameters = firebase.get('/Parameters',None )
	except:
		logger.info('Error reading parameters to Firebase')
		return Parameters
		
	Parameters = UpdateParameters(NewParameters,Parameters,Temps)
	return Parameters
	
def UpdateParameters(NewParameters,Parameters,Temps)
	#Loop through each key, see what changed
	for k in NewParameters.keys():
		if k == 'target':
			if float(Parameters[k]) != float(NewParameters[k]):
				logger.info('New Parameters: %s -- %f (%f)', k,float(NewParameters[k]),Parameters[k])
				Control.setTarget(float(NewParameters[k]))
				Parameters[k] = float(NewParameters[k])
		elif k == 'P' or k == 'I' or k == 'D':
			if float(Parameters[k]) != float(NewParameters[k]):
				logger.info('New Parameters: %s -- %f (%f)', k,float(NewParameters[k]),Parameters[k])
				Parameters[k] = float(NewParameters[k])
				Control.setGains(Parameters['P'],Parameters['I'],Parameters['D'])
		elif k == 'mode':
			if Parameters[k] != NewParameters[k]:
				logger.info('New Parameters: %s -- %s (%s)', k,NewParameters[k],Parameters[k])
				Parameters[k] = NewParameters[k]
				Parameters = SetMode(Parameters, Temps)

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
		Parameters['AugerOnTime'] = 15 #15
		Parameters['AugerOffTime'] = 55 #65
		
	elif Parameters['mode'] == 'Hold':
		G.SetState('fan',True)
		G.SetState('auger',True)
		CheckIgniter(Temps)
		Parameters['AugerOnTime'] = 20
		Parameters['AugerOffTime'] = min(max((436-Parameters['target'])/15.5,0),AugerOffMax) # T = -15.5(OffTime) + 436 
		
	WriteParameters(Parameters)	
	return Parameters	
		
def DoMode(Parameters,Temps):
	if Parameters['mode'] == 'Off':
		None
	
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

	#Auger currently on AND TimeSinceToggle > AugerOnTime
	if G.GetState('auger') and (time.time() - G.ToggleTime['auger']) > Parameters['AugerOnTime']:
		G.SetState('auger',False)
		CheckIgniter(Temps)
		WriteParameters(Parameters)
		
	#Auger currently off AND TimeSinceToggle > AugerOffTime
	if (not G.GetState('auger')) and (time.time() - G.ToggleTime['auger']) > Parameters['AugerOffTime']:
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
	if (time.time() - Control.LastUpdate) > ControlInterval:

		Avg = GetAverageSince(Temps,Control.LastUpdate)
		du = Control.update(Avg[1]) #Grill probe is [0] in T, [1] in Temps
		Parameters['AugerOffTime'] += du
		Parameters['AugerOffTime'] = max(min(Parameters['AugerOffTime'],AugerOffMax),0)
		logger.info('AugerOffTime %f',Parameters['AugerOffTime'])
		
		#Post control state
		D = {'time': time.time()*1000, 'P': Control.P, 'I': Control.I, 'D': Control.D, 'PID': Control.PID, 'Error':Control.error, 'Derv':Control.Derv, 'Inter':Control.Inter}
		try:			
			r = firebase.post_async('/Controls', D , params={'print': 'silent'}, callback=PostCallback)
		except:
			logger.info('Error writing Controls to Firebase')
		
		
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
LastParametersRead = time.time()

###############
#Main Loop    #
###############
while 1:
	CurrentTime = time.time()
	
	#Record temperatures
	Temps = RecordTemps(Temps)
		
	#Check for new parameters
	Parameters = ReadParameters(Parameters, Temps)

	#Do mode
	Parameters = DoMode(Parameters,Temps)
			
	time.sleep(TempInterval*0.9)
