<br />
<div align="center">
  <a href="https://github.com/sadkellz/External-Melee-Camera/">
    <img src="imgs/emc_logo.png"  width="400">
  </a>

<h1 align="center">External Melee Camera</h1>
</div>

## Description

**EMC** is a Blender add-on that integrates the ability to control various Melee and Dolphin functions from within Blender.  
This tool primarily focuses on camera functions, but is able to load states, play/pause, and create image sequences as well.

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
> > This will start controlling Melee's camera from Blender. To stop, press _'Q'_.
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
> > Will attempt to preview a sequence by loading the last state saved, and stepping through the frame range of Blender.


## Contact
[Twitter](https://twitter.com/sadkellz)

## License

This project is licensed under the GPL 3.0 License - see the LICENSE.md file for details

## Acknowledgments
[Slippi](https://slippi.gg/)

[Dolphin Freelook Manipulator For Blender 2.8](https://github.com/John10v10/-Useless-DolphinToolForBlender)

