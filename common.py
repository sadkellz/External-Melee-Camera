import psutil
from ctypes import *
from ctypes.wintypes import *


def dol_proc():
    process_name = "Slippi Dolphin"
    pid = None

    for proc in psutil.process_iter():
        if process_name in proc.name():
            pid = proc.pid
    return pid


# https://docs.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-writeprocessmemory
def process_ops(pid, addr, buf, bufSize, bytesWritten):
    k32 = WinDLL('kernel32', use_last_error=True)
    PROCESS_ALL_ACCESS = 0x1F0FFF

    OpenProcess = k32.OpenProcess
    OpenProcess.argtypes = [DWORD, BOOL, DWORD]
    OpenProcess.restype = HANDLE

    processHandle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)

    CloseHandle = k32.CloseHandle
    CloseHandle.argtypes = [HANDLE]
    CloseHandle.restype = BOOL

    WriteProcessMemory = k32.WriteProcessMemory
    WriteProcessMemory.argtypes = [HANDLE, LPCVOID, LPVOID, c_size_t, POINTER(c_size_t)]
    WriteProcessMemory.restype = BOOL
    WriteProcessMemory(processHandle, addr, c_char_p(buf), len(bufSize), byref(bytesWritten))

    CloseHandle(processHandle)
