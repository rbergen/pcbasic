# PC-BASIC #

> ## Notes about this version ##
>
> This is a modified version of PC-BASIC, maintained by [Rutger van Bergen](https://github.com/rbergen). This version includes the possibility to enable the devices (disks, parallel ports, serial ports) in PC-BASIC in read-only mode. 
>
> ### Motivation ###
>
> PC-BASIC emulates GW-BASIC, a BASIC version that was first released in 1983, the latest version of which was released in 1988. In that period, harddisk sizes were measured in megabytes, and often fit within two digits. A basic version of the MS-DOS operating system fit on a 360KB floppy, and GW-BASIC itself was 59KB in size. Also, computers were not permanently connected to the Internet. That is to say: things were simpler then, or at least easier to keep track of. GW-BASIC's security model (effectively absent) was in line with that.
>
> PC-BASIC provides GW-BASIC programs access to systems of today, running operating systems that are close to 20GB in size and consist of thousands of files. This makes that accidental or intential changes to key files are much harder to detect. Internet access is omnipresent and always-on, and even that is available to programs in PC-BASIC through serial ports. I feel that for this context, the GW-BASIC security model is not sufficient. Old GW-BASIC programs simply weren't written to deal with the context they're now confronted with. New programs could be deliberately malicious, and may well not be vetted to the same extent that other types of executable code are. It is for that reason that I added the ability to enable and mount devices in PC-BASIC in such a way that data can be pulled in, but not written out. It allows me to let PC-BASIC loose on all of its context, without files being broken or data going places it shouldn't.
>
> ### Status ###
>
> Before and after implementing the read-only device feature I communicated with Rob Hagemens, the author of PC-BASIC, about the idea and offered it for inclusion in the official version of PC-BASIC. In the end, Rob decided not to include it. His considerations can be found in [this discussion](https://github.com/robhagemans/pcbasic/discussions/186) and [this pull request](https://github.com/robhagemans/pcbasic/pull/188). This means that this extension to PC-BASIC is not part of the official codebase and not supported by its author.
>
> ### Installation and use ###
>
> This version of PC-BASIC does not come with installers. This means that the following steps must be taken to use it:
>
> 1. Clone the repo from GitHub:
>
>    ```text
>    git clone --recursive https://github.com/rbergen/pcbasic.git
>    ```
>
> 2. Enter the PC-BASIC directory and compile the documentation:
>
>    ```text
>    cd pcbasic
>    pip install Pillow lxml markdown
>    python -m packaging build_docs
>    ```
>
> 3. Run PC-BASIC directly from the source directory:
>
>    On Windows: `.\pc-basic`
>
>    On Linux/MacOS: `./pc-basic`
>
> To allow the use of the graphical interface with smooth fonts on Windows, I've created a ZIP file that contains the SDL2 and SDL2_gfx libraries for 32-bit and 64-bit versions of Windows. It can be downloaded using [this link](https://rbergen.home.xs4all.nl/pcbasic-libs.zip). The contents of the ZIP file should be unpacked into the "main" PC-BASIC directory, that being the one you changed into in step 2. As I don't own a computer running MacOS, I have not been able to include MacOS libraries in the ZIP file.
>
> ### Documentation ###
>
> The documentation for the `disable-writes` configuration or command-line option is embedded in the documentation that was generated in step 3 of [Installation and use](#installation-and-use) and can then be found in the file `PC-BASIC_documentation.html` in the `doc` directory.
>
> ### Maintenance policy (or at least, intent) ###
>
> At the time of writing (July 1, 2022), this branch is tracking [the develop branch of PC-BASIC](https://github.com/robhagemans/pcbasic/tree/develop). I intend to switch to tracking the [master branch](https://github.com/robhagemans/pcbasic/tree/master) as soon as the next PC-BASIC version is released (current version is 2.0.4). I'll try to update my read-only device branch as quickly as possible after PC-BASIC itself is updated, but I cannot give any guarantees about the speed at which I will be able to do so. Feel free to open an issue on this repository (i.e. [my fork](https://github.com/rbergen/pcbasic)) if you find I'm lagging behind.
>
> ### Support and interaction ###
>
> First off, whatever you do, **please don't ask Rob Hagemans for information about or support on the read-only device feature**. The code is not in his PC-BASIC codebase by his explicit choice.
>
> If you run into problems you can open [an issue on my fork](https://github.com/rbergen/pcbasic/issues). Similarly, if you want to discuss the feature's implementation, configuration, use, etc. then please start [a discussion on my fork](https://github.com/rbergen/pcbasic/discussions). There is one exception to that last sentence: you can contribute to the conversation about read-only devices in the context of PC-BASIC in [the existing discussion on the topic](https://github.com/robhagemans/pcbasic/discussions/186) in the upstream repository.
>  

## Description

_A free, cross-platform emulator for the GW-BASIC family of interpreters._

PC-BASIC is a free, cross-platform interpreter for GW-BASIC, Advanced BASIC (BASICA), PCjr Cartridge Basic and Tandy 1000 GWBASIC.
It interprets these BASIC dialects with a high degree of accuracy, aiming for bug-for-bug compatibility.
PC-BASIC emulates the most common video and audio hardware on which these BASICs used to run.
PC-BASIC runs plain-text, tokenised and protected .BAS files.
It implements floating-point arithmetic in the Microsoft Binary Format (MBF) and can therefore
read and write binary data files created by GW-BASIC.  

PC-BASIC is free and open source software released under the GPL version 3.  

See also the [PC-BASIC home page](http://robhagemans.github.io/pcbasic/).

![](https://robhagemans.github.io/pcbasic/screenshots/pcbasic-2.0.png)

----------

### Quick Start Guide ###

This quick start guide covers installation and elementary use of PC-BASIC. For more information, please refer to the [PC-BASIC documentation](http://pc-basic.org/doc/2.0#).

If you find bugs, please [open an issue on GitHub](https://github.com/robhagemans/pcbasic/issues). It would be most helpful if you could include a short bit of BASIC code that triggers the bug.


#### Installation ####

PC-BASIC desktop installers for Windows, Mac, and Linux can be downloaded from [GitHub](https://github.com/robhagemans/pcbasic/releases).

Python users can obtain the PC-BASIC package from [PyPI](https://pypi.org/project/pcbasic/) through `pip3 install pcbasic`.


#### BASIC survival kit ####
PC-BASIC has a 1980s-style interface operated by executing
typed commands. There is no menu, nor are there any of the visual clues
that we've come to expect of modern software.  

A few essential commands to help you get around:  

| Command               | Effect                                                        |
|-----------------------|---------------------------------------------------------------|
| `FILES`               | show current working directory and its contents               |
| `LOAD "PROGRAM"`      | loads the program file named `PROGRAM.BAS` into memory        |
| `LIST`                | displays the BASIC code of the current program                |
| `RUN`                 | starts the current program                                    |
| `SAVE "PROGRAM",A`    | saves the current program to a text file named `PROGRAM.BAS`  |
| `NEW`                 | immediately deletes the current program from memory           |
| `SYSTEM`              | exits PC-BASIC immediately, discarding any unsaved program    |

Use one of the key combinations `Ctrl+Break`, `Ctrl+Scroll Lock`, `Ctrl+C` or `F12+B`
to interrupt a running program.  


#### Program location ####
If started through the start-menu shortcut, PC-BASIC looks for programs in the shortcut's start-in folder.

- On **Windows**, this is your `Documents` folder by default.
- On **Mac** and **Linux** this is your home directory `~/` by default.

If started from the command prompt, PC-BASIC looks for programs in the current working directory.

See [the documentation on accessing your drives](http://pc-basic.org/doc/2.0#mounting) for more information.


#### External resources ####
See the [collection of GW-BASIC programs and tutorials](https://github.com/robhagemans/hoard-of-gwbasic).  
