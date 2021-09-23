from pywinauto import Application

app = Application(backend="uia").connect(path=r"C:\users\fores\appdata\roaming\slippi launcher\playback\Slippi Dolphin.exe", visible_only=False)
#dlg = app['Faster Melee - Slippi(2.3.6) - Playback']
dlg_spec = app['Faster Melee - Slippi(2.3.6) - Playback']
dlg_spec.minimize()
app.window(best_match='Faster Melee - Slippi(2.3.6) - Playback', visible_only=False).restore()
#restore()
#list = app.windows()
#app.Dialog.dump_tree()
#prop = dlg.EmulationMenuItem.items()
#print(prop)

#app['Faster Melee - Slippi (2.3.6) - PlaybackDialog']['ScrShot'].click()
#dlg.menu_select("Emulation->Load State->Last 1")
#dlg.get_items()
#dlg.Emulation.print_control_identifiers()
#app['EmulationMenuItem'][]

#dlg.menu_select("Emulation -> Load State")
#dlg.Load_State.MenuItem14.select()

#app.print_control_indentifiers()

#sub_items[0].select()