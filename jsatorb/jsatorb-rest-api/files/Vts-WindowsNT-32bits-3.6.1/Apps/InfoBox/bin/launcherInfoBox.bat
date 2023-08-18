@rem ---------------------------------------------------------------------------
@rem launcherInfoBox.bat
@rem
@rem HISTORIQUE
@rem VERSION : 3.5 : DM : VTS 2020 (S2) : 14/12/2020 : VTS 3.5
@rem VERSION : 3.2 : FA : FA_437 : 07/12/2017 : InfoBox ne se lance pas si le port est different de 8888
@rem VERSION : 3.1.1 : FA : FA_401 : 10/03/2017 : Regression VTS 3.1 : Pb avec les fichiers accentués
@rem VERSION : 3.1 : DM : DM_385 : 06/02/2017 : Passage à Qt5
@rem VERSION : 3.0 : FA : FA_350 : 05/07/2016 : Problème de démarrage d'Infobox à cause des accents dans le path
@rem VERSION : 2.7 : DM : DM_234 : 15/07/2015 : Création du plugin InfoBox
@rem FIN-HISTORIQUE
@rem Copyright © (2020) CNES All rights reserved
@rem ---------------------------------------------------------------------------

@rem Input parameter %1 is the path to the VTS project file
@rem Input parameter %2 is the client application ID
@rem Input parameter --serverport is optionnal (8888 by default)

@rem Need to switch to codepage 65001 (UTF-8) in order to correctly handle non-english characters. 
@rem (default is the historical DOS-850. Might use Windows-1250 but UTF-8 is the VTS standard.
@set PATH=%PATH%;%SystemRoot%\system32
@chcp 65001 > nul
@ECHO OFF

REM Default server port 
SET serverport=8888
SET vtsconfig=%1
SET appid=%2
SHIFT & SHIFT

:loop
IF NOT "%1"=="" (
    IF "%1"=="--serverport" (
        SET serverport=%2
        SHIFT
    )
    SHIFT
    GOTO :loop
)


@echo %appid% %vtsconfig% %appid% --serverport %serverport% --closeondisconnected

@rem End of file
 
