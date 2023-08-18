@rem ---------------------------------------------------------------------------
@rem cleanerSurfaceView.bat
@rem
@rem HISTORIQUE
@rem VERSION : 3.5 : DM : VTS 2020 (S2) : 14/12/2020 : VTS 3.5
@rem VERSION : 3.1 : DM : DM_385 : 06/02/2017 : Passage à Qt5
@rem VERSION : 3.0 : DM : DM_300 : 05/07/2016 : Généralisation de la fenêtre 2D
@rem VERSION : 2.7 : DM : DM_225 : 15/07/2015 : 2dWin : chargement dynamique des tuiles
@rem FIN-HISTORIQUE
@rem Copyright © (2020) CNES All rights reserved
@rem
@rem Suppression des répertoires temporaires de VTS
@rem ---------------------------------------------------------------------------

@echo off

@rem Parcours des options
for %%p in (%*) do (

   @rem Traitement de l'option de nettoyage
   if "%%p"=="--clear" (
   
      @rem Suppression des répertoires du cache WMS
      cd %~dp0/..
      for /d %%i in (cache.*) do (
         rd /s /q "%%i"
      )
      cd %~dp0
   )
)

@rem Code retour
exit /B 0

@rem End of file
