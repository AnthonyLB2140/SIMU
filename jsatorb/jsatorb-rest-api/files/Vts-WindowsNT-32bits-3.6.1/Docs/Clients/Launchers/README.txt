VTS Launcher Examples
=====================

Application launchers
~~~~~~~~~~~~~~~~~~~~~
The goal of a VTS application launcher is to prepare the visualization 
for a client application. 

It does not launch the application itself (as this is done by the Broker), 
instead it may pre-process visualization data, generate scripts, copy files, etc..

The ouput of a VTS launcher must be the command line arguments for the
client application. 

Essentially: 
1. Broker executes Launcher with specific input parameters (see below)
2. Launcher does any pre-process on visualization data 
3. Launcher outputs the command line arguments of the Application
4. Broker reads the Launcher output
5. Broker launch Application with arguments printed by Launcher

For more information please refer to the "Application launchers" section in 
the VTS User Manual.


Launcher input
--------------
Launchers are started by the Broker with the following command-line arguments:

<projectFile.vts> <appID> [--serverport <port>] [--datadir <dataDir>] [--tempdir <tempDir>]

    - <projectFile.vts>     is the absolute path to the VTS project file
    
    - <appID>               is the client application ID, which uniquely identifies the 
                            application during the visualization (used when there are 
                            several instances of the same application)
    
    - <port>                is an optional server port number. 
    
    - <dataDir>             is an optional directory that contains the data files for 
                            the project instead of the project file’s directory. 
                            Relative file names in the project file must then be resolved 
                            relative to this data directory. 
                            This is used by VTS when in read-only mode.
    
    - <tempDir>             is an optional temporary directory where all data from the 
                            launcher and its application should reside. 
                            This is used by VTS when in read-only mode.


Launcher output
---------------
The only mandatory output of a launcher is the command line arguments 
to be passed to its client application.
