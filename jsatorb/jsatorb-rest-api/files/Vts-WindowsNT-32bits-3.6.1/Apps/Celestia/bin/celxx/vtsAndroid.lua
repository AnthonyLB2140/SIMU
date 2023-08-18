--------------------------------------------------------------------------------
-- vtsAndroid.lua
--
-- Copyright © (2019) CNES All rights reserved
--
-- VER : $Id: vtsAndroid.lua 8957 2021-11-03 15:22:36Z mmo $
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- rotateQuatCameraAndroid
-- Fonction appelée à chaque réception de packet TCP de rotation de la caméra
--------------------------------------------------------------------------------

function rotateQuatCameraAndroid( sensorW, sensorX, sensorY, sensorZ, sensorTime )
   curCamRot = aCamera:getorientation()
   curSensRot = celestia:newrotation( sensorW, sensorX, sensorY, sensorZ ) 
   
   lastDataTime = os.clock()
   
   if( aCameraInit == true ) then 
      
      -- Initialisations date/quaternion
      firstSensorTime = sensorTime
      firstCelTime = lastDataTime

      -- Initialialisation des quaternions de référence
      -- Quaternion de référence du capteur
      referenceSensRot = curSensRot
      
      -- Quaternion de référence de la caméra
      referenceCamRot = aCamera:getorientation()
      
      -- Précalcul du quaternion de passage de Senseur->Camera : QsensRef^-1*QcamRef
      sensToCamRot = multQuat( invQuat( referenceSensRot ), referenceCamRot )
      
      -- Calcul de la rotation du senseur dans le repère caméra
      slerpRot = multQuat( curSensRot, sensToCamRot )

      -- Flags
      aCameraInit = false
      boolHookCodeAndroid = false   
      
   else
      -- Appel à chaque paquet réseau
      
      -- Temps de l'accelerometre dans le repère temporel Celestia
      endTime = sensorTime - firstSensorTime + firstCelTime 
      
      -- Correction si on dépasse la date courante
      if (endTime > lastDataTime) then
         firstCelTime = firstCelTime - endTime + lastDataTime
         endTime = sensorTime - firstSensorTime + firstCelTime
      end
      
      -- Ajout d'un paramètre utilisateur smooth
      endTime = endTime + 0.5
      
      startTime = lastDataTime
      startRot = slerpRot      

      -- Calcul de la rotation du senseur dans le repère caméra
      endRot = multQuat( curSensRot, sensToCamRot )
      
      boolHookCodeAndroid = true
   end
end


--------------------------------------------------------------------------------
-- hookTestCodeAndroid
-- Fonction appelée à chaque rendu de l'image de Celestia si demandé
--------------------------------------------------------------------------------

function hookTestCodeAndroid( dt )

   curTime = os.clock()
   
   if( curTime - endTime > 0 ) then
      -- Plus de données depuis 1 seconde : Celestia en idle ou perte connexion
      if( (curTime - endTime > 1) or ( curTime - lastDataTime > 1) ) then    
         -- Stoppe l'interpolation
         boolHookCodeAndroid = false
         -- Demande de réinit
         aCameraInit = true
         -- On se position à la date de fin pour arrêter d'interpoler
         curTime = endTime
      else 
         if( curTime - lastDataTime > 0 ) then
            -- On met à jour la fenêtre d'interpolation
            endTime = curTime + 0.5
            startTime = curTime
            startRot = slerpRot
         end
      end
   end
   
   -- Interpolation
   slerpRot = startRot:slerp( endRot, (curTime-startTime) / (endTime-startTime) )
   aCamera:setorientation( slerpRot )
end


--------------------------------- End Of File ----------------------------------
