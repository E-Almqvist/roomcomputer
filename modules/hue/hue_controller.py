import requests as req # Used for HTTP requests for the Hue API
import json # API uses JSON
import asyncio # ASync stuff
import time

from .lib.func import * # useful functions

from modules.configloader.loader import readconfig # used to read the config files
from os.path import expanduser # to get the home dir

homedir = expanduser("~") # get the home directory of the current user

IP_FETCH_URL = "http://discovery.meethue.com/" # returns the HUE bridges local IP

LIGHTS = {} # dictionary of all the lights
CONFIG = {} # the configuration 
PRESETS = {} # the presets
BRIDGE_ADDRESS = ""

loop = asyncio.get_event_loop() # ASync loop

def genUrl(params: str):
	return f"http://{BRIDGE_ADDRESS}/api/{CONFIG['username']}{params}" 

class APIrequest:

	def fetchBridgeIP():
		try:
			apiReq = req.get(IP_FETCH_URL)
			data = apiReq.json()
			return data[0]["internalipaddress"]

		except req.exceptions.RequestException as err:
			print("Unable to fetch HUE Bridge IP!")
			print(err)
			exit()

	# Get Req
	async def get( dest: str="", payload: str="" ):
		try:
			apiReq = req.get( genUrl(dest), data = payload )

			if( apiReq.status_code != 200 ): # print out the error if the status code is not 200
				print(apiReq)
				print(apiReq.text)

			return apiReq

		except req.exceptions.RequestException as err:
			print(err)

	# PUT Req
	async def put( dest: str="", payload: str="" ):
		try:
			apiReq = req.put( genUrl(dest), data = payload ) # send the payload

			if( apiReq.status_code != 200 ):
				print(apiReq)
				print(apiReq.text)

			return apiReq

		except req.exceptions.RequestException as err:
			print(err)


class controller:

	# Internal get functions
	async def getLights():
		return await APIrequest.get("/lights")

	async def getLight(index: int=1):
		return await APIrequest.get( "/lights/" + str(index) )

	# Lower level light manipulation (async)
	async def toggleLight(index: int=1, isOn: bool=True):
		await APIrequest.put( "/lights/" + str(index) + "/state", '{"on":' + boolToString(isOn) + '}' )

	async def toggleLights(isOn: bool=True):
		for key in LIGHTS:
			await controller.toggleLight(key, isOn)

	async def setLightRGB( index: int, r:int, g:int, b:int ):
		h, s, v = rgbToHsv(r, g, b)
		payload = '{"sat":' + str(s) + ', "bri":' + str(v) + ', "hue":' + str(h) + '}'

		await APIrequest.put( "/lights/" + str(index) + "/state", payload )

	# Normal functions
	def switchLight( index: int=1 ):
		key = LIGHTS.get(str(index))
		if(key):
			if( key.get("state") ):
				curPower = LIGHTS[str(index)]["state"]["on"]
				loop.run_until_complete( controller.toggleLight(index, not curPower))
		else:
			print("Error: Light index '" + str(index) + "' out of range")

	def switchLights():
		for key in LIGHTS:
			controller.switchLight(key)

	# Light control
	def setLightColor( index:int, r:int, g:int, b:int ):
		if( LIGHTS.get(str(index)) ):
			loop.run_until_complete( controller.setLightRGB(index, r, g, b) )
		else:
			print("Error: Light index '" + str(index) + "' out of range")

	def setLightBrightness( index:int, b:int ):
		if( LIGHTS.get(str(index)) ):
			payload = '{"bri":' + str(b) + '}'
			loop.run_until_complete( APIrequest.put( "/lights/" + str(index) + "/state", payload ) )
		else:
			print("Error: Light index '" + str(index) + "' out of range")

	def setBrightness( b:int ):
		for key in LIGHTS:
			controller.setLightBrightness( key, b )

	def setAllLightsColor( r:int, g:int, b:int ):
		for key in LIGHTS:
			controller.setLightColor( key, r, g, b )

	def Power(isOn:bool=True): # Controlling the power of the lights
		loop.run_until_complete( controller.toggleLights(isOn) )

	def powerLight( index:int, isOn:bool=True ):
		loop.run_until_complete( controller.toggleLight( index, isOn ) )

	# Presets
	def setLightPreset( index:int, p:str ):
		if( LIGHTS.get(str(index)) ):
			if( PRESETS.get(p) ):
				preset = PRESETS[p]
				r, g, b = preset["color"]
				brightness = preset["brightness"]

				controller.setLightColor( index, r, g, b )
				controller.setLightBrightness( index, brightness )
			else:
				print("Error: Unknown preset '" + p + "'")
		else:
			print("Error: Light index '" + str(index) + "' out of range")

	def setPreset( presetID:str, index:int=-1 ):
		if( PRESETS.get(presetID) ):
			if( index == -1 ):
				for key in LIGHTS:
					controller.setLightPreset( key, presetID )
			else:
				controller.setLightPreset( index, presetID )
		else:
			print("Error: Unknown preset '" + presetID + "'")

	def countLights():
		return len(LIGHTS)

	# Controller "system" functions
	def delay(n:int):
		time.sleep(n)

	def init( cfgPath=f"{homedir}/.config/roomcomputer/config.json", presetPath=f"{homedir}/.config/roomcomputer/presets.json" ):
		config = readconfig(cfgPath)
		presets = readconfig(presetPath)

		global CONFIG
		CONFIG = config["hue"]

		global PRESETS
		PRESETS = presets

		global BRIDGE_ADDRESS
		# If there is no address in the config then get it via the API
		if( "address" in CONFIG ):
			BRIDGE_ADDRESS = CONFIG["address"]
		else:
			BRIDGE_ADDRESS = APIrequest.fetchBridgeIP()

		try:
			jsonLights = loop.run_until_complete(APIrequest.get("/lights"))
			global LIGHTS
			LIGHTS = json.loads(jsonLights.text)
		except Exception as err:
			print("\033[91mUnable to fetch lights. This could be because your configuration file is incomplete! Please check your config at \"~/.config/roomcomputer/config.json\".\033[0m")
			raise err

	def end():
		loop.close()
