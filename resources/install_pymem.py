import subprocess
import sys
import os

python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
target = os.path.join(sys.prefix, 'lib', 'site-packages')

subprocess.call([python_exe, '-m', 'ensurepip'])
subprocess.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'])

subprocess.call([python_exe, '-m', 'pip', 'install', '--upgrade', 'pymem', '-t', target])

print('FINISHED')