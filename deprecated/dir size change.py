from pathlib import Path
from time import sleep
import time

root_directory = Path('C://Users//fores//AppData//Roaming//Slippi Launcher//playback//User//ScreenShots//GALE01')

while True:
    size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    sleep(0.5)
    size2 = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())
    if size == size2:
        break

