#!/usr/bin/env python
# from lib.input import * # Commandline parser

import sys

from modules.hue import hue_controller as hue # Actual controller 

cmd = "hue"

def help():
	print("--Help page--")

	print( "'" + cmd + "' : Display this help page" )
	print( "'" + cmd + " light (index)' ... : Specify light target, from 1-" + str(hue.controller.countLights()) )
	print( "'" + cmd + " lights' ... : Specify all lights\n" )

	print("--Commands--")
	print( "'on'/'off' : Turn light(s) on/off" )
	print( "'switch' : Switch the light(s) power" )
	print( "'set ...'" )
	print( "	'preset (preset ID)' : Set the preset (from presets.py)" )
	print( "	'color (red) (green) (blue)' : Set the color, from 0-255" )
	print( "	'brightness (brightness)' : Set the brightness, from 0-255" )

	print("\nExamples:\n'hue light 2 on' : Turn on light 2\n'hue lights set color 255 255 255' : Set all lights colors to white")

boolConvert = {
	"on": True,
	"off": False
}

# this is the most spaghetti-ish code I have ever written but it works

def parseCommand( cmd:list, pos:int, index=-1, displayHelp=True ):
	try:
		if( cmd[pos] == "on" or cmd[pos] == "off" ):
			if( index == -1 ):
				hue.controller.Power( boolConvert[cmd[pos]] )
			else:
				hue.controller.powerLight( index, boolConvert[cmd[pos]] )

			return

		elif( cmd[pos] == "switch" ):
			if(index == -1):
				hue.controller.switchLights()
			else:
				hue.controller.switchLight(index)

			return

		elif( cmd[pos] == "set" ):
			if( cmd[pos+1] == "preset" ):
				hue.controller.setPreset( cmd[pos+2], index )
				return

			elif( cmd[pos+1] == "color" ):
				if( len(cmd) > pos+4 ):
					r, g, b = int(cmd[pos+2]), int(cmd[pos+3]), int(cmd[pos+4])

					if( index == -1 ):
						hue.controller.setAllLightsColor( r, g, b ) # this code is bad
					else:
						hue.controller.setLightColor( index, r, g, b )

					return
				else:
					print("Error: Missing parameters")
					help()

			elif( cmd[pos+1] == "brightness" ):
				if( len(cmd) > pos+2 ):
					bri = int(cmd[pos+2])

					if( index == -1 ):
						hue.controller.setBrightness(bri)
					else:
						hue.controller.setLightBrightness( index, bri )

					return
		help() # display help if function did nothing

	except (RuntimeError, TypeError, NameError, IndexError) as err:
		if(displayHelp):
			help() # display the help page if parameters are missing (it will give out an IndexError)

		print( "\n\nError: " + str(err) )


def parseCommandline( cmd=sys.argv, needHelp=True ):
	if( len(cmd) > 1 ):
		if( cmd[1] == "light" ):
			parseCommand( cmd, 3, cmd[2], displayHelp=needHelp )

		elif( cmd[1] == "lights" ):
			parseCommand( cmd, 2, displayHelp=needHelp )
	elif( needHelp ):
		help()
