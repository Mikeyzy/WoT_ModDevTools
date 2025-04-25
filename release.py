import os, shutil, subprocess
import ClientData.utility._cmdargs as _cmdargs

DIR_ROOT = os.path.dirname(os.path.abspath(__file__))
DIR_TEMP = os.path.join(DIR_ROOT, 'temp')
DIR_RELEASE = os.path.join(DIR_ROOT, 'Release')

PATH_RELEASED_PACKAGE = os.path.join(DIR_RELEASE, f'Wot_ModDevTools_V{_cmdargs.VERSION}.zip')
PATH_7Z = os.path.join(DIR_ROOT, '7z', 'x64', '7za.exe')

ignorePattern = shutil.ignore_patterns("__pycache__")

if __name__ == '__main__':
	lData = [
		'ClientData',
		'Python27',
		'7z',
		'LICENSE.txt',
		'Readme.txt',
	]

	# clean temp dir
	if os.path.isdir(DIR_TEMP):
		print(f'Cleaning temp dir: {DIR_TEMP}')
		shutil.rmtree(DIR_TEMP)
	os.makedirs(DIR_TEMP)

	for item in lData:
		print(f'Copying {item}')
		if os.path.isdir(os.path.join(DIR_ROOT, item)):
			shutil.copytree(os.path.join(DIR_ROOT, item), os.path.join(DIR_TEMP, f'Wot_ModDevTools_V{_cmdargs.VERSION}', item), ignore=ignorePattern)
		elif os.path.isfile(os.path.join(DIR_ROOT, item)):
			shutil.copyfile(os.path.join(DIR_ROOT, item), os.path.join(DIR_TEMP, f'Wot_ModDevTools_V{_cmdargs.VERSION}', item))
	
	if os.path.isfile(PATH_RELEASED_PACKAGE):
		print(f'Removing existing release package: {PATH_RELEASED_PACKAGE}')
		os.remove(PATH_RELEASED_PACKAGE)
	cmd7z = f'"{PATH_7Z}" a -tzip -mx9 "{PATH_RELEASED_PACKAGE}" "{DIR_TEMP}\\*"'
	subprocess.run(cmd7z, encoding='utf-8')

	print(f'Release package created: {PATH_RELEASED_PACKAGE}')
