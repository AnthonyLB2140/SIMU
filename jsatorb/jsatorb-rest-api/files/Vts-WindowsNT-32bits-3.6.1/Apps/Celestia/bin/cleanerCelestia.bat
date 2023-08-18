@rem ---------------------------------------------------------------------------
@rem cleanerCelestia.bat
@rem
@rem Copyright © (2020) CNES All rights reserved
@rem
@rem Suppression des répertoires temporaires de VTS
@rem ---------------------------------------------------------------------------


@echo off 

for %%p in (%*) do (
   @rem Suppression des répertoires temporaires
   if "%%p"=="--clear" (
      for /d %%a in (%~dp0/extras_*) do rd /s /q "%%a"

      @rem Code retour
      exit /B 0
   )
)

@rem End of file
