import _cmdargs
import json, os, re, subprocess, threading, traceback, shutil
from typing import Any, Dict, List, Tuple, Union

VERBOSE_LEVEL: int = _cmdargs.ARGUMENTS.verbose

VERBOSE_ALL = 0
VERBOSE_INFO = 1
VERBOSE_WARNING = 2
VERBOSE_ERROR = 3
VERBOSE_PROGRESS = 4

_DICT_VERBOSE_LEVEL = {
	VERBOSE_ALL: 'All',
	VERBOSE_INFO: 'Info',
	VERBOSE_WARNING: 'Warning',
	VERBOSE_ERROR: 'Error',
	VERBOSE_PROGRESS: 'Progress'
}

_verbosLock = threading.Lock()

def verboseOutput(*args, src: str = 'Main', level: int = VERBOSE_INFO, **kw):
	if level >= VERBOSE_LEVEL:
		_verbosLock.acquire()
		print(f'[{src}:{_DICT_VERBOSE_LEVEL.get(level, "Other")}]:', *args, **kw)
		_verbosLock.release()

STR_DEFAULT_CONFIG = \
r'''{
	"path" :{
		"7z": "..\\..\\7z",
		"python27": "..\\..\\python27",
		"wot": "..\\..\\..\\World of Tanks"
	},
	"workflow": {
		"extract": {
			"overwrite": false,
			"multithread": true,
			"pkgs":[
				"gui-part1.pkg",
				"gui-part2.pkg",
				"gui-part3.pkg",
				"scripts.pkg"
			]
		},
		"decompile": {
			"overwrite": false,
			"multithread": true,
			"output": "scripts_d",
			"pythonPathUseDecompiled": true
		}
	},
	"multithread": {
		"limit": -1
	}
}'''

DIR_ROOT: str = os.path.dirname(os.path.abspath(__file__))
PATH_CONFIG: str = os.path.join(DIR_ROOT, 'utilityConfig.json')

DICT_CONFIG: Dict[str, Dict[str, Any]] = json.loads(STR_DEFAULT_CONFIG)
if os.path.isfile(PATH_CONFIG):
	try:
		with open(PATH_CONFIG, 'r', encoding='utf-8') as f:
			DICT_CONFIG = json.load(f)
		verboseOutput(f'Loaded config file: {PATH_CONFIG}', level=VERBOSE_INFO)
	except Exception as e:
		verboseOutput(f'Error loading config file: {PATH_CONFIG}', level=VERBOSE_ERROR)
		verboseOutput(traceback.format_exc(), level=VERBOSE_ERROR)
else:
	verboseOutput(f'No config file found, generating default config file: {PATH_CONFIG}', level=VERBOSE_INFO)
	with open(PATH_CONFIG, 'w', encoding='utf-8') as f:
		f.write(STR_DEFAULT_CONFIG)
	verboseOutput('You may want to change some settings in the config file', level=VERBOSE_INFO)

DIR_7Z: str = ''
DIR_PYTHON27: str = ''
DIR_WOT_CLIENT: str = ''
PATH_UNCOMPYLE6: str = ''

try:
	if len(os.path.splitdrive(DICT_CONFIG['path']['7z'])[0]):
		# abs path
		DIR_7Z = DICT_CONFIG['path']['7z']
	else:
		# rel path
		DIR_7Z = os.path.abspath(os.path.join(DIR_ROOT, DICT_CONFIG['path']['7z']))
	if len(os.path.splitdrive(DICT_CONFIG['path']['python27'])[0]):
		# abs path
		DIR_PYTHON27 = DICT_CONFIG['path']['python27']
	else:
		# rel path
		DIR_PYTHON27 = os.path.abspath(os.path.join(DIR_ROOT, DICT_CONFIG['path']['python27']))
	if len(os.path.splitdrive(DICT_CONFIG['path']['wot'])[0]):
		# abs path
		DIR_WOT_CLIENT = DICT_CONFIG['path']['wot']
	else:
		# rel path
		DIR_WOT_CLIENT = os.path.abspath(os.path.join(DIR_ROOT, DICT_CONFIG['path']['wot']))
	for node, path in (('7z', DIR_7Z), ('python27', DIR_PYTHON27), ('wot', DIR_WOT_CLIENT)):
		if not os.path.isdir(path):
			verboseOutput(f'Config path.{node} is not pointing to a valid directory {path}', level=VERBOSE_ERROR)
	PATH_UNCOMPYLE6 = os.path.join(DIR_PYTHON27, 'Scripts', 'uncompyle6.exe')
except Exception as e:
	verboseOutput(f'Error loading config file: {PATH_CONFIG}', level=VERBOSE_ERROR)
	verboseOutput(traceback.format_exc(), level=VERBOSE_ERROR)
	raise e

def updateConfig():
	global DIR_7Z, DIR_PYTHON27, DIR_WOT_CLIENT, PATH_UNCOMPYLE6
	try:
		with open(PATH_CONFIG, 'w', encoding='utf-8') as f:
			json.dump(DICT_CONFIG, f, indent='\t')
		verboseOutput('Config file updated', level=VERBOSE_INFO)
		if len(os.path.splitdrive(DICT_CONFIG['path']['7z'])[0]):
			# abs path
			DIR_7Z = DICT_CONFIG['path']['7z']
		else:
			# rel path
			DIR_7Z = os.path.abspath(os.path.join(DIR_ROOT, DICT_CONFIG['path']['7z']))
		if len(os.path.splitdrive(DICT_CONFIG['path']['python27'])[0]):
			# abs path
			DIR_PYTHON27 = DICT_CONFIG['path']['python27']
		else:
			# rel path
			DIR_PYTHON27 = os.path.abspath(os.path.join(DIR_ROOT, DICT_CONFIG['path']['python27']))
		if len(os.path.splitdrive(DICT_CONFIG['path']['wot'])[0]):
			# abs path
			DIR_WOT_CLIENT = DICT_CONFIG['path']['wot']
		else:
			# rel path
			DIR_WOT_CLIENT = os.path.abspath(os.path.join(DIR_ROOT, DICT_CONFIG['path']['wot']))
		for node, path in (('7z', DIR_7Z), ('python27', DIR_PYTHON27), ('wot', DIR_WOT_CLIENT)):
			if not os.path.isdir(path):
				verboseOutput(f'Config path.{node} is not pointing to a valid directory {path}', level=VERBOSE_ERROR)
		PATH_UNCOMPYLE6 = os.path.join(DIR_PYTHON27, 'Scripts', 'uncompyle6.exe')
	except Exception as e:
		verboseOutput(f'Error updating config file: {PATH_CONFIG}', level=VERBOSE_ERROR)
		verboseOutput(traceback.format_exc(), level=VERBOSE_ERROR)
		raise e

MIN_FILE_PER_WORKER = 32

repWinFileVersion = re.compile(r'(\d+)\.(\d+)\.(\d+)\.(\d+)')

def listAllFiles(dirPath: str, fileExt: str=None, dirBlacklist: List[str]=None) -> List[str]:
	lFiles = []
	for item in os.listdir(dirPath):
		if os.path.isfile(os.path.join(dirPath, item)):
			if fileExt is not None:
				if not item.endswith(fileExt):
					continue
			lFiles.append(os.path.join(dirPath, item))
		elif os.path.isdir(os.path.join(dirPath, item)):
			if dirBlacklist is not None:
				if item in dirBlacklist:
					continue
			lFiles.extend(listAllFiles(os.path.join(dirPath, item), fileExt, dirBlacklist))
	return lFiles

class WinFileVersion:
	major: int
	minor: int
	build: int
	release: int

	def __init__(self, major: int, minor: int, build: int, release: int):
		self.major = major
		self.minor = minor
		self.build = build
		self.release = release
	
	def __str__(self):
		return f'{self.major}.{self.minor}.{self.build}.{self.release}'

	def __repr__(self):
		return f'WinFileVersion({self.major}, {self.minor}, {self.build}, {self.release})'

	def __eq__(self, other):
		if isinstance(other, WinFileVersion):
			return self.major == other.major and self.minor == other.minor and self.build == other.build and self.release == other.release
		elif isinstance(other, str):
			return str(self) == other
		else:
			return False

	@classmethod
	def fromString(cls, strVersion: str):
		matches = repWinFileVersion.match(strVersion)
		if matches:
			return cls(int(matches.group(1)), int(matches.group(2)), int(matches.group(3)), int(matches.group(4)))
		else:
			return None

	@classmethod
	def fromFileVersionData(cls, dataMsw: int, dataLsw: int):
		return cls(dataMsw >> 16, dataMsw & 0xFFFF, dataLsw >> 16, dataLsw & 0xFFFF)

class DecompileWorker(threading.Thread):
	_lPycFiles: List[str]
	_fileCount: int
	_errorCount: int
	_dirOutput: str
	_completed: bool = False
	verboseLevel: int = 0

	def __init__(self, pycFiles: List[str], dirOutput: str, fileStart: int, fileEnd: int, verboseLevel: int = 0, *args, **kw):
		kw.pop('daemon', None)
		kw.pop('name', None)
		super().__init__(daemon=True, name=f'DecompileWorker<{fileStart}-{fileEnd}>', *args, **kw)
		self._lPycFiles = pycFiles
		self._fileCount = len(pycFiles)
		self._dirOutput = dirOutput
		self.verboseLevel = verboseLevel

	def _verboseOutput(self, msg: str, level: int = 0) -> None:
		if self.verboseLevel <= level:
			verboseOutput(msg, src=self.name, level=level)

	def run(self) -> None:
		successCount = 0
		dirScripts = os.path.join(os.path.dirname(self._dirOutput), 'scripts')
		for pathFile in self._lPycFiles:
			scriptOutput = os.path.join(self._dirOutput, os.path.relpath(pathFile[:-1], dirScripts))
			# self._verboseOutput(f'Decompile {pathFile} to {scriptOutput}', level=VERBOSE_INFO)
			rc = subprocess.run(f'"{PATH_UNCOMPYLE6}" -o "{scriptOutput}" "{pathFile}"', capture_output=True, encoding='utf-8')
			if rc.returncode != 0:
				self._verboseOutput(f'Error occurred during decompiling "{pathFile}", exit code: {rc.returncode}', level=VERBOSE_ERROR)
				if rc.returncode == 3221225725:
					# recursion limit
					self._verboseOutput('Recursion limit exceeded', level=VERBOSE_ERROR)
				else:
					self._verboseOutput('Failed to decompile', level=VERBOSE_ERROR)
				os.rename(scriptOutput, scriptOutput + '_error')
				shutil.copyfile(pathFile, scriptOutput+'c')
			else:
				successCount += 1
		self._errorCount = self._fileCount - successCount
		if self._errorCount > 0:
			self._verboseOutput(f'Decompiled {successCount}/{len(self._lPycFiles)} pyc files', level=VERBOSE_INFO)
		else:
			if len(self._lPycFiles) > 1:
				self._verboseOutput(f'Decompiled {self._lPycFiles[0]} and {len(self._lPycFiles)-1} more pyc files', level=VERBOSE_INFO)
			else:
				self._verboseOutput(f'Decompiled {self._lPycFiles[0]}', level=VERBOSE_INFO)
		self._completed = True

	@property
	def completed(self) -> bool:
		return self._completed
	
	@property
	def errorCount(self) -> int:
		return self._errorCount

	@property
	def fileCount(self) -> int:
		return self._fileCount

__all__ = ['DIR_ROOT', 'PATH_CONFIG', 'DICT_CONFIG', 'DIR_7Z', 'DIR_PYTHON27', 'DIR_WOT_CLIENT', 'PATH_UNCOMPYLE6', 'VERBOSE_ALL', 'VERBOSE_INFO', 'VERBOSE_WARNING', 'VERBOSE_ERROR', 'VERBOSE_PROGRESS', 'STR_DEFAULT_CONFIG', 'listAllFiles', 'verboseOutput', 'WinFileVersion', 'DecompileWorker']