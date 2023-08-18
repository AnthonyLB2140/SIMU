@rem ---------------------------------------------------------------------------
@rem launcherMinimalClient.bat
@rem 
@rem This is an example of an application launcher (script).
@rem
@rem See README.txt for more information.
@rem ---------------------------------------------------------------------------

@rem Need to switch to codepage 65001 (UTF-8) in order to correctly handle 
@rem non-english characters. (default is the historical DOS-850. 
@rem Might use Windows-1250 but UTF-8 is the VTS standard.
@chcp 65001 > nul

@rem ---------------------------------------------------------------------------
@rem 1. Read input arguments (see README.txt)
@rem ---------------------------------------------------------------------------
set appid=%2

@rem ---------------------------------------------------------------------------
@rem 2. Do any pre-process work as neeeded
@rem ---------------------------------------------------------------------------


@rem ---------------------------------------------------------------------------
@rem 3. Output application arguments (used by the Broker to launch the application)
@rem    NOTE: launchers must always output the application ID first
@rem ---------------------------------------------------------------------------

@rem Launcher allows us to adapt Broker arguments to our application arguments
@rem Here we only use the application ID and ignore all other arguments

@echo %appid% --appid %appid%

@rem End of file
 
