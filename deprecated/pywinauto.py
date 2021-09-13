app = Application().connect(process=1788)
win = app['Faster Melee - Slippi(2.3.6) - Playback']
win.set_focus()
keyboard.send_keys("{VK_F3 down}"
                    "{VK_F3 up}")


def sync_frame_end():
    DevCamAddress = bpy.context.scene.cam_mem_address
    pid = int(DevCamAddress[:8], 16)
    app = Application().connect(process=pid)
    win = app['Faster Melee - Slippi(2.3.6) - Playback']
    if bpy.ops.screen.frame_jump(end=False):
        win.set_focus()
        keyboard.send_keys("{VK_F3 down}"
                            "{VK_F3 up}")

# Automatic PID
import psutil

PROCNAME = "Slippi Dolphin.exe"

for proc in psutil.process_iter(['pid']):
    if proc.name() == PROCNAME:
        pid = int(str(proc.pid), 16)
        break