#!python3
import _cmdargs
import os, argparse, shutil, subprocess, sys, time, traceback
from typing import List

if sys.version_info.major < 3 or sys.version_info.minor < 8:
	print('This script requires Python 3.8 or higher')
	sys.exit(1)

parser = argparse.ArgumentParser(os.path.basename(__file__), description='World of Tanks Mod Dev Tools - Client Unpacker')
parser.add_argument('-v', '--verbose', dest='verbose', nargs='?', type=int, const=0, default=2, help='Set verbosity level (1=Info, 2=Warning[Default], 3=Error, 4=Progress)')
parser.add_argument('-r', '--reset-config', dest='reset', action='store_true', default=False, help='Reset config file to default and exit')
parser.add_argument('-o', '--overwrite', dest='overwrite', action='store', default='a', help='Overwrite action when prompt (y=overwrite, n=skip, a=ask[Default])')
parser.add_argument('--dir-python', dest='dirPython', action='store', default=None, help='Set path to python27 directory')
parser.add_argument('--dir-7z', dest='dir7z', action='store', default=None, help='Set path to 7z directory')
parser.add_argument('--dir-wot', dest='dirWot', action='store', default=None, help='Set path to World of Tanks client directory')
parser.add_argument('-V', '--version', action='version', version=f'World of Tanks Mod Dev Tools - Client Unpacker V{_cmdargs.VERSION}')

_cmdargs.ARGUMENTS = parser.parse_args()

print(_cmdargs.BANNER_STARTUP)

import _shared

if _cmdargs.ARGUMENTS.reset:
	# reset config file
	with open(_shared.PATH_CONFIG, 'w', encoding='utf-8') as file:
		file.write(_shared.STR_DEFAULT_CONFIG)
	print('Config file reset to default')
	sys.exit(0)

import win32api

settingChanged = False
if _cmdargs.ARGUMENTS.dirPython is not None:
	if os.path.isdir(_cmdargs.ARGUMENTS.dirPython):
		settingChanged = True
		_shared.DICT_CONFIG['path']['python27'] = _cmdargs.ARGUMENTS.dirPython

if _cmdargs.ARGUMENTS.dir7z is not None:
	if os.path.isdir(_cmdargs.ARGUMENTS.dir7z):
		settingChanged = True
		_shared.DICT_CONFIG['path']['7z'] = _cmdargs.ARGUMENTS.dir7z

if _cmdargs.ARGUMENTS.dirWot is not None:
	if os.path.isdir(_cmdargs.ARGUMENTS.dirWot):
		settingChanged = True
		_shared.DICT_CONFIG['path']['wot'] = _cmdargs.ARGUMENTS.dirWot

if settingChanged:
	_shared.updateConfig()

DIR_DATA = os.path.dirname(_shared.DIR_ROOT)
DIR_WOT_PKG = os.path.join(_shared.DIR_WOT_CLIENT, 'res', 'packages')
PATH_WOT_EXE = os.path.join(_shared.DIR_WOT_CLIENT, 'WorldOfTanks.exe')

PATH_7Z = os.path.join(_shared.DIR_7Z, 'x64', '7za.exe')

DICT_WORKFLOW = _shared.DICT_CONFIG["workflow"]

PKG_TO_EXTRACT = DICT_WORKFLOW["extract"]["pkgs"]
PKG_EXTRACT_OVERWRITE = DICT_WORKFLOW["extract"]["overwrite"]
PKG_EXTRACT_MULTITHREAD = DICT_WORKFLOW["extract"]["multithread"]

DECOMPILE_OUTPUT = DICT_WORKFLOW["decompile"]["output"]
DECOMPILE_OVERWRITE = DICT_WORKFLOW["decompile"]["overwrite"]
DECOMPILE_MULTITHREAD = DICT_WORKFLOW["decompile"]["multithread"]
THREAD_LIMIT = int(os.getenv('NUMBER_OF_PROCESSORS', '4'))

CMD_7Z_EXTRACT = f'"{PATH_7Z}" ''x -mmt -tzip -y "{PATH_FILE}" -o"{DIR_OUTPUT}"'

VERBOSE_LEVEL = 0

STR_PROGRESS_DISPLAY = r'-\|/'

if __name__ == '__main__':
	tsStart = time.monotonic()
	# get client version
	fInfo = win32api.GetFileVersionInfo(PATH_WOT_EXE, '\\')
	gameVersion = _shared.WinFileVersion.fromFileVersionData(fInfo['ProductVersionMS'], fInfo['ProductVersionLS'])
	dirOutput = os.path.join(DIR_DATA, str(gameVersion), 'res')
	_shared.verboseOutput('Extract Packages Output Dir:', dirOutput, level=_shared.VERBOSE_PROGRESS)
	# unpack packages
	unpackPkg = True
	if os.path.isdir(dirOutput):
		if PKG_EXTRACT_OVERWRITE:
			_shared.verboseOutput('Cleaning Extract Packages Output Dir', level=_shared.VERBOSE_PROGRESS)
			shutil.rmtree(dirOutput)
		else:
			# ask user overwrite
			print('Extract Packages Output Dir already exists!')
			if _cmdargs.ARGUMENTS.overwrite.lower()[0] == 'y':
				sIn = 'y'
				print('Overwriting...')
			elif _cmdargs.ARGUMENTS.overwrite.lower()[0] == 'n':
				sIn = 'n'
				print('Skipping...')
			else:
				sIn = input('Overwrite? (y/n): ').lower() + 'n'
			if sIn[0] == 'y':
				_shared.verboseOutput('Cleaning Extract Packages Output Dir', level=_shared.VERBOSE_PROGRESS)
				shutil.rmtree(dirOutput)
			else:
				unpackPkg = False
	iProg = 0
	if unpackPkg:
		_shared.verboseOutput('Start Extracting Packages', level=_shared.VERBOSE_PROGRESS)
		os.makedirs(dirOutput, exist_ok=True)
		# extract packages
		lPkgPath = [os.path.join(DIR_WOT_PKG, pkg) for pkg in PKG_TO_EXTRACT]
		lPInfo: List[tuple[str, subprocess.Popen]] = []
		lenPkg = len(lPkgPath)
		pkgExtracted = 0
		# for pkgFile in PKG_TO_EXTRACT:
		# 	pathPkg = os.path.join(DIR_WOT_PKG, pkgFile)
		# 	# print(CMD_7Z_EXTRACT.format(PATH_FILE=pathPkg, DIR_OUTPUT=dirOutput))
		# 	print('Start Extracting', pkgFile)
		# 	lPInfo.append((pkgFile, subprocess.Popen(CMD_7Z_EXTRACT.format(PATH_FILE=pathPkg, DIR_OUTPUT=dirOutput), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')))
		while len(lPkgPath) + len(lPInfo):
			if PKG_EXTRACT_MULTITHREAD:
				if len(lPkgPath) and len(lPInfo) < THREAD_LIMIT:
					pathPkg = lPkgPath.pop(0)
					print('\r', end='')
					_shared.verboseOutput('Start Extracting', pathPkg)
					lPInfo.append((pathPkg, subprocess.Popen(CMD_7Z_EXTRACT.format(PATH_FILE=pathPkg, DIR_OUTPUT=dirOutput), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')))
					continue
				# _shared.verboseOutput(f'Extracting progress: {pkgExtracted/lenPkg*100:>6.2f}%  ', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
				i = 0
				while i < len(lPInfo):
					if lPInfo[i][1].poll() is not None:
						pkg, p = lPInfo.pop(i)
						print('\r', end='')
						_shared.verboseOutput(f'Extracted {pkg}, exit code: {p.returncode}')
						_shared.verboseOutput(f'Extracting progress: {pkgExtracted/lenPkg*100:>6.2f}% {STR_PROGRESS_DISPLAY[iProg]}\r', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
						pkgExtracted += 1
					else:
						i += 1
				_shared.verboseOutput(f'Extracting progress: {pkgExtracted/lenPkg*100:>6.2f}% {STR_PROGRESS_DISPLAY[iProg]}\r', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
				iProg += 1
				if iProg > 3:
					iProg = 0
				time.sleep(0.2)
			else:
				pathPkg = lPkgPath.pop(0)
				_shared.verboseOutput('Extracting', pathPkg, end='', flush=True)
				rc = subprocess.run(CMD_7Z_EXTRACT.format(PATH_FILE=pathPkg, DIR_OUTPUT=dirOutput), capture_output=True, encoding='utf-8')
				_shared.verboseOutput(f'\rExtracted {pathPkg}, exit code: {rc.returncode}')
		_shared.verboseOutput('\nAll Packages Extracted', level=_shared.VERBOSE_PROGRESS)
	# decompile pyc files
	dirScripts = os.path.join(dirOutput, 'scripts')
	if not os.path.isdir(dirScripts):
		_shared.verboseOutput('Scripts not extracted, skip decompile', level=_shared.VERBOSE_PROGRESS)
	else:
		dirScriptsOutput = os.path.join(dirOutput, DECOMPILE_OUTPUT)
		dirScriptsLibOutput = os.path.join(dirOutput, '_python_builtin')
		decompilePyc = True
		_shared.verboseOutput('Decompile pyc files to:', dirScriptsOutput, level=_shared.VERBOSE_PROGRESS)
		if os.path.isdir(dirScriptsOutput):
			if DECOMPILE_OVERWRITE or _cmdargs.ARGUMENTS.overwrite:
				_shared.verboseOutput('Cleaning Decompile Output Dir', level=_shared.VERBOSE_PROGRESS)
				shutil.rmtree(dirScriptsOutput)
			else:
				# ask user overwrite
				print('Decompile Output Dir already exists!')
				if _cmdargs.ARGUMENTS.overwrite.lower()[0] == 'y':
					sIn = 'y'
					print('Overwriting...')
				elif _cmdargs.ARGUMENTS.overwrite.lower()[0] == 'n':
					sIn = 'n'
					print('Skipping...')
				else:
					sIn = input('Overwrite? (y/n): ').lower() + 'n'
				if sIn[0] == 'y':
					_shared.verboseOutput('Cleaning Decompile Output Dir', level=_shared.VERBOSE_PROGRESS)
					shutil.rmtree(dirScriptsOutput)
				else:
					decompilePyc = False
		if decompilePyc:
			_shared.verboseOutput('Start Decompiling', level=_shared.VERBOSE_PROGRESS)
			_shared.verboseOutput('Pyc Source Dir:', dirScripts, level=_shared.VERBOSE_PROGRESS)
			_shared.verboseOutput('Decompile Output Dir:', dirScriptsOutput, level=_shared.VERBOSE_PROGRESS)
			# p = subprocess.Popen(f'"{PATH_UNCOMPYLE6}" -r -o "{dirScriptsOutput}" "{dirScripts}"', encoding='utf-8')
			# while p.poll() is None:
			# 	time.sleep(0.1)
			# print('Decompile exit code:', p.returncode)
			# get all pyc files that need to be decompiled, ignore Lib and site-packages directories since they are python standard libs
			lFiles = _shared.listAllFiles(dirScripts, '.pyc', ['Lib', 'site-packages'])
			lenFiles = len(lFiles)
			fileCompiled = 0
			i = 0
			lWorkers: List[_shared.DecompileWorker] = []
			# DECOMPILE_MULTITHREAD = False # DEBUG
			while i < lenFiles + len(lWorkers):
				if DECOMPILE_MULTITHREAD:
					if i < lenFiles and len(lWorkers) < THREAD_LIMIT:
						print('\r', end='')
						_shared.verboseOutput(f'Start decompiling file {i}-{min(i+THREAD_LIMIT, lenFiles)}    ')
						worker = _shared.DecompileWorker(lFiles[i:i+THREAD_LIMIT], dirScriptsOutput, fileStart=i, fileEnd=min(i+THREAD_LIMIT, lenFiles), verboseLevel=VERBOSE_LEVEL)
						worker.start()
						lWorkers.append(worker)
						i += THREAD_LIMIT
						continue
					j = 0
					while j < len(lWorkers):
						if lWorkers[j].completed:
							worker = lWorkers.pop(j)
							fileCompiled += worker.fileCount
							print('\r', end='')
							_shared.verboseOutput(f'Decompiled file {fileCompiled}/{lenFiles}, error count: {worker.errorCount}     ')
							_shared.verboseOutput(f'Decompiling progress: {fileCompiled/lenFiles*100:>6.2f}% {STR_PROGRESS_DISPLAY[iProg]}\r', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
						else:
							j += 1
					_shared.verboseOutput(f'Decompiling progress: {fileCompiled/lenFiles*100:>6.2f}% {STR_PROGRESS_DISPLAY[iProg]}\r', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
					iProg += 1
					if iProg > 3:
						iProg = 0
					time.sleep(0.2)
				else:
					_shared.verboseOutput(f'Decompiling file {f"{i}-{min(i+THREAD_LIMIT, lenFiles)}":>12}, {min(i/lenFiles, 1)*100:>6.2f}%\r', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
					worker = _shared.DecompileWorker(lFiles[i:i+THREAD_LIMIT], dirScriptsOutput, fileStart=i, fileEnd=min(i+THREAD_LIMIT, lenFiles), verboseLevel=VERBOSE_LEVEL)
					worker.start()
					worker.join() # wait for worker to finish
					_shared.verboseOutput(f'Decompiling file {f"{i}-{min(i+THREAD_LIMIT, lenFiles)}":>12}, {min((i+THREAD_LIMIT)/lenFiles, 1)*100:>6.2f}%\r', end='', flush=True, level=_shared.VERBOSE_PROGRESS)
					i += THREAD_LIMIT
			_shared.verboseOutput('Copying wot python builtin Lib...', level=_shared.VERBOSE_PROGRESS)
			shutil.copytree(os.path.join(dirScripts, 'common', 'Lib'), os.path.join(dirScriptsLibOutput, 'Lib'))
			_shared.verboseOutput('Copying wot python site-packages...', level=_shared.VERBOSE_PROGRESS)
			shutil.copytree(os.path.join(dirScripts, 'common', 'site-packages'), os.path.join(dirScriptsLibOutput, 'site-packages'))
			_shared.verboseOutput('Updating python import path files...', level=_shared.VERBOSE_PROGRESS)
			try:
				with open(os.path.join(_shared.DIR_PYTHON27, 'wotImports.pth'), 'w', encoding='utf-8') as file:
					file.write(f'# World of Tanks V{str(gameVersion)} decompiled imports\n')
					for item in os.listdir(dirScriptsOutput):
						if os.path.isdir(os.path.join(dirScriptsOutput, item)):
							file.write(f'{os.path.join(dirScriptsOutput, item)}\n')
					file.write(f'{os.path.join(dirScriptsLibOutput, "Lib")}\n')
					file.write(f'{os.path.join(dirScriptsLibOutput, "site-packages")}\n')
			except Exception as e:
				_shared.verboseOutput(traceback.format_exc(), level=_shared.VERBOSE_ERROR)
			_shared.verboseOutput('\nAll pyc files decompiled', level=_shared.VERBOSE_PROGRESS)
	_shared.verboseOutput(f'\nWorkflow complete for WOT V{str(gameVersion)}', level=_shared.VERBOSE_PROGRESS)
	sTotal = time.monotonic() - tsStart
	minutes, seconds = divmod(sTotal, 60)
	_shared.verboseOutput(f'Elapsed Time: {int(minutes)}:{seconds:.3f}\n', level=_shared.VERBOSE_PROGRESS)
	print(_cmdargs.BANNER_EXIT)