================ World of Tanks Mod Dev Tools Readme ================

This package is designed to help you to create your own World of Tanks mod.

It contains the following tools:
	1. Client Unpacker
		- [ClientData/utility/clientUnpacker.py]
		- Extract selected data files from the game client.
		- Decompile game scripts.
	2. Python 2.7 64 bit (Same as WoT Python version)
		- [Python27]
		- Necessary for decompiling game scripts.

***Dependencies***
	To run Client Unpacker, you will need Python 3.8 or higher.
	You can download it from https://www.python.org/

In [ClientData/utility], you will find clientUnpacker.py,
this will help you to extract game data and decompile game scripts.

Run it with option -r will generate a default config file [ClientData/utility/clientUnpacker.cfg]
In this file you can setup necessary parameters for Client Unpacker to work correctly.

Here is the default config file:
{
	# path config
	"path" :{
		# path to 7z dir, 7-Zip download: standalone console version
		"7z": "..\\..\\7z",
		# path to Python 2.7 dir
		"python27": "..\\..\\python27",
		# path to World of Tanks game dir
		"wot": "..\\..\\..\\World of Tanks"
	},
	# workflow config
	"workflow": {
		"extract": {
			# overwrite existing files
			"overwrite": false,
			# enable multithreaded extraction
			"multithread": true,
			# pkg files to extract
			"pkgs":[
				"gui-part1.pkg",
				"gui-part2.pkg",
				"gui-part3.pkg",
				"scripts.pkg"
			]
		},
		"decompile": {
			# overwrite existing files
			"overwrite": false,
			# enable multithreaded decompilation
			"multithread": true,
			# decompiled scripts output dir
			"output": "scripts_d",
			# use decompiled scripts instead of pyc
			"pythonPathUseDecompiled": true
		}
	},
	"multithread": {
		# number of threads
		# -1=All threads
		# 0=Single thread
		# int=Number of threads
		# float<0~1>=Percentage of all threads
		"limit": -1
	}
}

After necessary changes, you can run Client Unpacker directly
to extract game data and decompile game scripts.
It will output to [ClientData/<gameVersion>] dir.

for more advanced usage, run Client Unpacker with option -h

================ Release Notes ================

V1.0.0 - Initial release
	Python 2.7 64 bit with necessary packages for decompiling game scripts
	Client Unpacker for automating extracting game data and decompiling game scripts

