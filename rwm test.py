from ReadWriteMemory import ReadWriteMemory

rwm = ReadWriteMemory()

process = rwm.get_process_by_name('Dolphin.exe')
process.open()

print('\nPrint the Process information.')
print(process.__dict__)
pause_state_pointer = process.get_pointer(0x7FFFFFFF)

pause_state = process.read(pause_state_pointer)

print('\nPrinting the current values.')
print({'Pause': pause_state})

#process.write(pause_state_pointer, (10))

#pause_state = process.read(pause_state_pointer)

process.close()
