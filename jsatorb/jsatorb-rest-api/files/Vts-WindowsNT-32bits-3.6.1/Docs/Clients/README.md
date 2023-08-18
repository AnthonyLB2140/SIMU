# README

This directory contains examples of minimal VTS client applications.

The goal is to show you how to:
* Connect to VTS Broker as an external application
* Display TIME messages sent by the Broker

For more information on the VTS Protocol, please refer to the VTS User Manual.

These examples are provided "as is" without warranty of any kind. Please refer
to the VTS Licence

Feel free to use it in your project and to let us know if you have any comment
or suggestion.

* CNES: thomas.crosnier@cnes.fr
* SPACEBEL: vts-team@spacebel.fr


## Requirements

* Python client: Python interpreter (https://www.python.org/downloads/)

* TCL client: tclsh and tcllib (https://www.tcl.tk/software/tcltk/)

* Java client:
    - JDK (http://www.oracle.com/technetwork/java/javase/downloads/index.html)
    - Sources must be compiled into a jar file:
      `$ javac fr/cnes/Main.java fr/cnes/VTSConnection.java`
      `$ jar cvmf META-INF/MANIFEST.MF minimalClient.jar fr/cnes`


## How to use

### As a VTS external application

1. Start VTS and open a VTS project
2. Start VTS Broker (Ctrl+R or Project/Run)
3. Launch minimal VTS client application with default parameters

### As a VTS project application

In order to use the minimal VTS client application as a project application 
(defined in your VTS project) you need to compile it. 

On Windows, you can use :
    - Python client: py2exe for Python client 
    - TCL client: freewrap or KBS (Kitgen Build System)

1. Drop your compiled minimalclient(.exe) into MinimalClient/bin directory
2. Copy launchers scripts from the Launchers directory to MinimalClient/bin
3. Copy the MinimalClient directory into VTS 'Apps' directory
4. Launch VTS and load your VTS project
5. Add your application (`Right-click` under Applications > Add Application)
6. Start visualization (Project > Run)
