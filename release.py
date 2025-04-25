import os, sys
import ClientData.utility._cmdargs as _cmdargs

DIR_ROOT = os.path.dirname(os.path.abspath(__file__))
DIR_RELEASE = os.path.join(DIR_ROOT, 'Release')

PATH_RELEASED_PACKAGE = os.path.join(DIR_RELEASE, f'Wot_ModDevTools_V{_cmdargs.VERSION}.zip')

if __name__ == '__main__':
	lData = [
		'ClientData',
		'Python27',
		'7z',
		'LICENSE.txt',
		'Readme.txt',
	]