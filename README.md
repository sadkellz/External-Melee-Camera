<br />
<div align="center">
  <a href="https://github.com/sadkellz/External-Melee-Camera/">
    <img src="imgs/emc_logo.png"  width="400">
  </a>

<h1 align="center">External Melee Camera</h1>
</div>

## Description

**EMC** is a Blender add-on that enables you to control various functions in Super Smash Bros. Melee and Dolphin directly from Blender. 

It mainly focuses on camera controls, but it also allows you to load states, toggle play/pause, and generate image sequences.

Consider supporting me on Ko-fi, this project took a lot of time and effort and I would appreciate the tips!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/C0C5FL4PH)
## Getting Started

>### Requirements
>* [Pymem](https://pymem.readthedocs.io/en/latest/)
>* [Blender 3.1+](https://www.blender.org/download/) - Not tested on earlier versions.
>* [Slippi](https://slippi.gg/)

## Installing the Add-on
>### Pymem
>To install **Pymem**, open Blender and navigate to the scripting menu.
>
>![](imgs/Scripting_Menu.png)
>
>Click open, and locate [_install_pymem.py_]()
>
>![](imgs/Scripting_Menu_2.png)
>
>Once opened, run the script.
>
>![](imgs/Scripting_Menu_3.png)
###
>### External Melee Camera
>Navigate to your Blender preferences by going to _'Edit > Preferences'_
>
>![](imgs/Preferences_Menu.png)
>
>Head to the _'Add-ons'_ tab and click _'Install...'_
>
>![](imgs/Install_Addon.png)
>
>Locate _External-Melee-Camera.zip_ and click _Install Add-on_
> 
>![](imgs/Install_Addon_2.png)

#

## Scene Setup
> ### Blender File
> To get started, open the provided [emc_stages.blend]() file. This Blender scene contains all of the legal stages
> in their own collections, to be used as reference when creating a camera animation.
> #### _NOTE: Dolphin must be running for the panel to appear!_
> ![](imgs/Panel.png)
> 
> ### Descriptions
> > ##### Sync Camera
> > 
> > This feature allows you to control the camera in Super Smash Bros. Melee using Blender. Press _'Q'_ to disable camera control.
> 
> > ##### Save State
> > 
> > This creates a Dolphin save state. Will overwrite the oldest state.
> 
> > ##### Load State
> > 
> > Loads the last saved state.
> >
> 
> > ##### Image Sequence
> > 
> > Loads the last state saved, and starts saving screenshots in Dolphin for the duration of Blenders frame range.
> > These images can be found at  
> > `C:\Users\*your name*\AppData\Roaming\Slippi Launcher\playback\User\ScreenShots`
> 
> > ##### Preview Sequence
> > 
> > Will attempt to preview a sequence by loading the last state saved, and steps through the frame range of Blender.
>
> > ##### Sync Media Controls
> > This function will toggle the play/pause state of Melee in sync with Blender's play/pause state.
> 
> > ##### Screenshot Directory
> > 
> > This is where you set the directory of where Dolphin saves screenshots to.
> > `C:\Users\*your name*\AppData\Roaming\Slippi Launcher\playback\User\ScreenShots`
>

## Contact
[Twitter](https://twitter.com/sadkellz)  
Discord: KELLZ#0001
## License

This project is licensed under the GPL 3.0 License - see the [LICENSE.md]() file for details

## Acknowledgments
[Slippi](https://slippi.gg/)

[Dolphin Freelook Manipulator For Blender 2.8](https://github.com/John10v10/-Useless-DolphinToolForBlender)

