--------------------------------------------------------------------------------
-- vtsCamera.lua
--
-- Copyright © (2020) CNES All rights reserved
--
-- VER : $Id: vtsCamera.lua 8969 2021-11-09 14:28:16Z jee $
--------------------------------------------------------------------------------


local table = table

-- Table globale des paramètres de tracking
-- et initialisation des flags d'état
trackingParameters={
   step1complete = false,
   step2complete = false,
   step3complete = false,
   canBeSaved = false }

-- * Liste des paramètres :

-- trackingParameters.from
-- trackingParameters.initialOrientation
-- trackingParameters.to
-- trackingParameters.finalOrientation
-- trackingParameters.duration
-- trackingParameters.startInterpolation
-- trackingParameters.endInterpolation
-- trackingParameters.accelTime
-- trackingParameters.trackingToString
-- trackingParameters.initialToString
-- trackingParameters.step1complete
-- trackingParameters.step2complete
-- trackingParameters.step3complete
-- trackingParameters.canBeSaved


------ CelObject class ------

CelObject = { }

function CelObject:new(o)
   o = o or {}
   setmetatable(o, self)
   self.__index = self
   return o
end
------ End CelObject Class ------



----------------------------------------------
-- Define global functions
----------------------------------------------
empty =
    function(obj)
        return     obj == nil or obj:name() == "?" or obj:type() == "null" ;
    end

zoomToFit =
   function()
       local obs = celestia:getobserver()
       local obsPos = obs:getposition()
       local sel = celestia:getselection()
       if empty(sel) then return end
       local selPos = sel:getposition()
       local dist = obsPos:distanceto(selPos)
       local rad = sel:radius()
       local appDia = 2*math.atan(rad/dist)
       obs:setfov(appDia*1.20)
   end;

customGoto =
   function(obj)
      -- Goto selection and make it fit the screen.
      local obs = celestia:getobserver()
      if empty(obj) == true then
          local sel = celestia:getselection()
          obj = sel;
      end
      local fov = obs:getfov()
      if empty(obj) == false then
          obs:follow(obj);
          obs:gotodistance(obj, 5.5 * obj:radius() / (fov / 0.4688), custom_goto_duration)
      end
   end;

-- Renvoie la structure d'un satellite VTS
getVTSSatellite =
   function( satelliteFullName )
      local satelliteName = string.gsub( satelliteFullName, ".*/", "" )
      for i, satStruct in pairs(gSatellites) do
         if( satelliteName == satStruct.name ) then
            return satStruct
         end
      end
      celestia:log( "VTS satellite \"" .. satelliteName .. "\" not found !" )
      return nil
   end;


-- Renvoie la structure d'un body VTS
getVTSBody =
   function( bodyName )
      for i, bodyStruct in pairs(gBodies) do
         if( bodyName == bodyStruct.name ) then
            return bodyStruct
         end
      end
      celestia:log( "VTS body " .. bodyName .. " not found !" )
      return nil
   end;

-- Convertit un chaÃ®ne de caratÃ¨re en latin 1 vers de l'UTF-8
latin1ToUTF8 =
   function( latin1Str )
      local count = string.len( latin1Str )
      local utf8Bytes = {}
      for i = 1, count do
         local latin1Byte = string.byte( latin1Str, i )
         if latin1Byte < 0x80 then
            table.insert( utf8Bytes, latin1Byte )
         else
            table.insert( utf8Bytes, 0xc0 | ( latin1Byte >> 6 ) )
            table.insert( utf8Bytes, 0x80 | ( latin1Byte & 0x3f ) )
         end
      end

      return string.char( table.unpack( utf8Bytes ) )
   end


-- Convertit une chaÃ®ne de caractÃ¨re en UTF8 vers du latin 1
UTF8ToLatin1 =
   function( utf8Str )
      local count = string.len( utf8Str )
      local latin1Bytes = {}
      local i = 1
      while  i <= count do
         local utf8Byte = string.byte( utf8Str, i )
         if utf8Byte < 0x80 then
            table.insert(latin1Bytes, utf8Byte)
         else
            local latin1Byte = ( utf8Byte & 0x3 ) << 6
            i = i + 1
            utf8Byte = string.byte( utf8Str, i )
            latin1Byte = latin1Byte | ( utf8Byte & 0x3F )
            table.insert(latin1Bytes, latin1Byte)
         end
         i = i + 1
      end

      return string.char( table.unpack( latin1Bytes ) )
   end


----------------------------------------------

--------------------------------------------------------------------------------
-- Variables globales pour la visualisation d'orbite
--------------------------------------------------------------------------------

-- Corps central par réfaut
gCentralBodyName = "Sol/Earth"

-- Satellite observé passé en variable globale entre les deux fonctions
satellite = nil

-- Y avait-il l'atmoshpère avant le scale ?
atmospheresWereHere = "unset" ;


--------------------------------------------------------------------------------
-- setCustomCamera
--
-- Restauration d'un caméra stockée dans un state VTS
--------------------------------------------------------------------------------

function setCustomCamera
(
   viewrow,
   viewcol,
   coordsysname,
   reference,
   target,
   posX,
   posY,
   posZ,
   quatW,
   quatX,
   quatY,
   quatZ,
   fov,
   camInfo
)
   local view = getObserverIndex( viewrow, viewcol )
   local obs = celestia:getobservers()[view]

   -- Repère
   local objReference = celestia:find( reference )
   if( objReference:type() == "null" ) then
      return
   end
   local objTarget = celestia:find( target )
   local obsFrame = celestia:newframe( coordsysname, objReference, objTarget )
   obs:setframe( obsFrame )

   -- Position
   local obsPos = celestia:newposition( posX, posY, posZ)
   obs:setposition( obsFrame:from( obsPos ) )

   -- Orientation
   local obsOrient = celestia:newrotation( quatW, quatX, quatY, quatZ )
   obs:setorientation( obsFrame:from( obsOrient ) )

   -- FOV
   obs:setfov( fov )

   -- Memorisation
   rt.lastReceivedCamera[view] = {}
   rt.lastReceivedCamera[view].coordsysname = coordsysname
   rt.lastReceivedCamera[view].reference = reference
   rt.lastReceivedCamera[view].target = target
   rt.lastReceivedCamera[view].posX = posX
   rt.lastReceivedCamera[view].posY = posY
   rt.lastReceivedCamera[view].posZ = posZ
   rt.lastReceivedCamera[view].quatW = quatW
   rt.lastReceivedCamera[view].quatX = quatX
   rt.lastReceivedCamera[view].quatY = quatY
   rt.lastReceivedCamera[view].quatZ = quatZ
   rt.lastReceivedCamera[view].fov = fov
   rt.lastReceivedCamera[view].camInfo = camInfo
end


--------------------------------------------------------------------------------
-- getCelestiaFullName
--
-- Renvoie un string contenant le nom complet d'un objet au format Celestia,
-- c'est-à-dire avec la concatenation du nom de tous ces parents.
--------------------------------------------------------------------------------

function getCelestiaFullName( object )
   local fullName = object:name()
   objectTable = object:getinfo()
   while( objectTable.parent ~= nil and objectTable.name ~= "Sun" and objectTable.name ~= "Sol" ) do
      fullName = objectTable.parent:name() .. "/" .. fullName
      objectTable = objectTable.parent:getinfo()
   end
   return fullName
end


--------------------------------------------------------------------------------
-- getCameraToString
--
-- Renvoie sous la forme d'une chaine de caractères la description complète des
-- la caméra courante. C'est la fonction inverse de setCustomCamera.
--------------------------------------------------------------------------------

function getCameraToString
(
)
   -- Parcours des vues
   local activecam = "Default"
   local camstrings = {}
   local observers = celestia:getobservers()
   for i = 1, rt.multi.h do
      for j = 1, rt.multi.v do
         local view = getObserverIndex( i, j )
         if( view <= #observers ) then
            -- Sérialisation de la caméra
            local obs = observers[view]
            local actual_frame = obs:getframe()
            local actual_coordsys = actual_frame:getcoordinatesystem()

            local refobj = actual_frame:getrefobject()
            local findRefObj = "nil"
            if refobj then
               findRefObj = getCelestiaFullName( refobj )
            end

            local tarobj = actual_frame:gettargetobject()
            local findTarObj = "nil"
            if tarobj then
               findTarObj = getCelestiaFullName( tarobj )
            end

            local actual_fov = obs:getfov()

            -- Conversion des position et orientation dans le repère local
            local actual_obspos = actual_frame:to( obs:getposition() )
            local actual_obsrot = actual_frame:to( obs:getorientation() )

            -- Comparaison avec la dernière caméra reçue pour savoir s'il y a eu des modifications
            -- Les modifications sont soit du fait de l'utilisateur à la souris, soit du fait de la
            -- réception d'une commande de caméra. Dans les deux cas, on invalide les infos
            local camInfo = ""
            if( rt.lastReceivedCamera[view] ~= nil ) then
               -- Si on a déjà reçu une caméra
               if( rt.lastReceivedCamera[view].camInfo ~= nil ) then

                  -- Si les paramètres textes sont identiques
                  if( rt.lastReceivedCamera[view].coordsysname     == actual_coordsys
                      and rt.lastReceivedCamera[view].reference    == findRefObj
                      and rt.lastReceivedCamera[view].target       == findTarObj ) then

                     -- Si les distances sont identiques
                     local normActual = math.sqrt( actual_obspos:getx() * actual_obspos:getx()
                                                 + actual_obspos:gety() * actual_obspos:gety()
                                                 + actual_obspos:getz() * actual_obspos:getz() )
                     local normReceived = math.sqrt( rt.lastReceivedCamera[view].posX * rt.lastReceivedCamera[view].posX
                                                   + rt.lastReceivedCamera[view].posY * rt.lastReceivedCamera[view].posY
                                                   + rt.lastReceivedCamera[view].posZ * rt.lastReceivedCamera[view].posZ )
                     -- Soit les deux normes sont nulles, soit la différence relative est très faible
                     if( (math.abs(normActual) < 1e-20 and math.abs(normReceived) < 1e-20 )
                          or ( math.abs(normActual - normReceived) <= 1e-5 * math.max(math.abs(normActual), math.abs(normReceived)) ) ) then

                        -- Si les directions sont identiques
                        local scalar = actual_obspos:getx() / normActual * rt.lastReceivedCamera[view].posX / normReceived
                                     + actual_obspos:gety() / normActual * rt.lastReceivedCamera[view].posY / normReceived
                                     + actual_obspos:getz() / normActual * rt.lastReceivedCamera[view].posZ / normReceived
                        if( math.abs( scalar ) >= 1 - 1e-5 ) then

                           -- Si l'angle entre les deux quaternions est très faible
                           local cosHalfTheta = actual_obsrot:real()*rt.lastReceivedCamera[view].quatW
                                              + actual_obsrot:imag():getx()*rt.lastReceivedCamera[view].quatX
                                              + actual_obsrot:imag():gety()*rt.lastReceivedCamera[view].quatY
                                              + actual_obsrot:imag():getz()*rt.lastReceivedCamera[view].quatZ
                           if( math.abs( cosHalfTheta ) >= 1 - 1e-5 / math.sin( obs:getfov()/2 ) ) then

                              -- Enfin, si le FOV est similaire
                              if( math.abs( rt.lastReceivedCamera[view].fov - obs:getfov() ) < 1e-5 ) then

                                 -- La caméra actuelle est celle que l'on a reçue par cameraDesc, on renvoie les infos
                                 camInfo = rt.lastReceivedCamera[view].camInfo

                              end
                           end
                        end
                     end
                  end
               end
            end

            -- Insertion tous les paramètres dans une chaine de caractères
            local cam = string.format( "\"%s\" \"%s\" \"%s\" %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %s",
                                       actual_coordsys, findRefObj, findTarObj,
                                       actual_obspos:getx(),
                                       actual_obspos:gety(),
                                       actual_obspos:getz(),
                                       actual_obsrot:real(),
                                       actual_obsrot:imag():getx(),
                                       actual_obsrot:imag():gety(),
                                       actual_obsrot:imag():getz(),
                                       obs:getfov(),
                                       camInfo )
            table.insert( camstrings, cam )

            -- Test d'observer actif
            if( obs == celestia:getobserver() ) then
               activecam = cam
            end
         end
      end
   end

   -- Traitement multiview
   if( #observers > 1 and #observers == rt.multi.h*rt.multi.v ) then
      return "multi " .. rt.multi.h .. " " .. rt.multi.v .. " " .. rt.multi.sep .. " " .. table.concat( camstrings, " " .. rt.multi.sep .. " " )
   else
      -- Singleview ou incohérence entre l'état multiview stocké et actuel : renvoi de la caméra active
      return activecam
   end
end


--------------------------------------------------------------------------------
-- setCameraPositionAndDirection
--
-- Fonction utilitaire positionnant la caméra à une distance d'un objet en fixant
-- sa direction et son vecteur up
--
-- Si distanceFromObjCenter est positif on regarde vers l'objet
-- Si distanceFromObjCenter est négatif on regarde à l'opposé de l'objet
--------------------------------------------------------------------------------

function setCameraPositionAndDirection( myObject, dirVector, upVector, distanceFromObjCenter )

   -- Repère de référence
   local viewerFrameOfRef = myObject:bodyfixedframe()

   -- Position de l'objet de référence
   local objCenter = myObject:getposition()

   -- Calcul du vecteur dans le système de coordonnées de Celestia
   local universalUp = viewerFrameOfRef:from( celestia:newrotation( 1, 0, 0, 0 ) ):transform( upVector )

   -- Calcul des positions caméra et cible
   dirVector = dirVector:normalize()
   local absDistanceFromObjCenter = math.abs( distanceFromObjCenter )
   local signDistanceFromObjCenter = distanceFromObjCenter > 0 and 1 or -1
   local cameraOffsetVector = celestia:newvector(
                                    dirVector:getx() * absDistanceFromObjCenter,
                                    dirVector:gety() * absDistanceFromObjCenter,
                                    dirVector:getz() * absDistanceFromObjCenter )
   local targetOffsetVector = celestia:newvector(
                                    dirVector:getx() * -1 * signDistanceFromObjCenter,
                                    dirVector:gety() * -1 * signDistanceFromObjCenter,
                                    dirVector:getz() * -1 * signDistanceFromObjCenter )
   local cameraPositionVector = viewerFrameOfRef:from(
                                 viewerFrameOfRef:to(objCenter)
                                 + cameraOffsetVector )
   local targetPositionVector = viewerFrameOfRef:from(
                                 viewerFrameOfRef:to(cameraPositionVector)
                                 + targetOffsetVector )

   -- Définition du repère de la caméra
   local obs = celestia:getobserver()
   obs:setframe( viewerFrameOfRef )

   -- Positionnement de l'observeur
   obs:setposition(cameraPositionVector)

   -- Caméra tournée dans la direction demandée avec son vecteur up
   obs:lookat(targetPositionVector, universalUp)

end


--------------------------------------------------------------------------------
-- vtsGetscreendimension
--
-- Cette fonction permet de donner les dimensions intérieures de l'écran. Elle
-- surcharge celestia:getscreendimension() car dans Cosmographia les modifications
-- ne sont pas immédiatement prises en compte.
--------------------------------------------------------------------------------

function vtsGetscreendimension()

   -- Utilisation de la taille qui vient d'être mémorisée
   if( rt.width ~= 0 ) then
      return rt.width, rt.height
   end

   -- Appel de la fonction normale
   return celestia:getscreendimension()
end


--------------------------------------------------------------------------------
-- setCameraSensorView
--
-- Caméra associée à un senseur.
--
-- Cette fonction place la caméra du point de vue du senseur. Le UP de la caméra
-- est vers X ou Y.
--------------------------------------------------------------------------------

function setCameraSensorView( sensorFullName, halfAngleOnX, halfAngleOnY, tovector, upvector, upname, margin )

   -- Sélection du senseur
   local sensorObject = celestia:find( sensorFullName )
   if( sensorObject:type() == "null" ) then
      return
   end

   -- Positionnement de la caméra
   setCameraPositionAndDirection( sensorObject, tovector, upvector, rt.sensorCamOffset )

   -- Calcul du ratio de la fenêtre
   local xWindow
   local yWindow
   xWindow, yWindow = vtsGetscreendimension()
   local ratioWindow = xWindow / yWindow

   -- Limitation des demi angles à 89.5° (contrainte tangente et FOV)
   halfAngleOnX = math.min( tonumber(halfAngleOnX), math.rad( 89.5 ) )
   halfAngleOnY = math.min( tonumber(halfAngleOnY), math.rad( 89.5 ) )

   -- Calcul du ratio du senseur
   local ratioSensor
   if( upname ~= "X" ) then
      ratioSensor = math.tan( halfAngleOnY ) / math.tan( halfAngleOnX )
   else
      ratioSensor = math.tan( halfAngleOnX ) / math.tan( halfAngleOnY )
   end

   -- Réglage de l'ouverture de la caméra sur l'ouverture du capteur
   local fov
   local obs = celestia:getobserver()
   if( ratioWindow > ratioSensor ) then

   -- Choix de l'angle en fonction du Up
      local halfAngle
      if( upname ~= "X" ) then
         halfAngle = halfAngleOnX
      else
         halfAngle = halfAngleOnY
      end

      -- Application d'une marge
      margedHalfAngleOnY = math.atan( (1 + margin / 100.) * math.tan( halfAngle ) )

      -- Le FOV de la commande setFov est appliqué directement
      fov = 2 * margedHalfAngleOnY

   else

      -- Choix de l'angle en fonction du Up
      local halfAngle
      if( upname ~= "X" ) then
         halfAngle = halfAngleOnY
      else
         halfAngle = halfAngleOnX
      end

      -- Application d'une marge
      margedHalfAngleOnX = math.atan( (1 + margin / 100.) * math.tan( halfAngle ) )

      -- Le FOV de la commande setFov est appliqué sur l'ouverture Y correspondante
      fov = 2 * math.atan( math.tan(margedHalfAngleOnX)/ratioWindow )
   end

   -- Les limites du FOV sont 0.001 et 179 mais les float en lua sont moins précis
   -- qu'en C++ donc on doit un peu plus restreindre
   fov = math.max( fov, math.rad( 0.002 ) )
   fov = math.min( fov, math.rad( 178.9 ) )

   -- Réglage du FOV
   obs:setfov( fov )

   -- Sélection du senseur
   celestia:select( sensorObject )
end


--------------------------------------------------------------------------------
-- setWindowSensorView
--
-- Dimensionne la fenêtre exactement à la dimension du senseur
--
-- Cette fonction place la caméra du point de vue du senseur. Le UP de la caméra
-- est vers X ou Y.
--------------------------------------------------------------------------------

function setWindowSensorView( sensorFullName, halfAngleOnX, halfAngleOnY, width, up )

   -- Sélection du senseur
   local sensorObject = celestia:find( sensorFullName )
   if( sensorObject:type() == "null" ) then
      return
   end

   -- Calcul de la taille des décorations de la fenêtre
   local xPos, yPos, widthPrev, heightPrev = celestia:getwindowinfos()
   local xWindow, yWindow = celestia:getscreendimension()
   local xDeco = widthPrev - xWindow
   local yDeco = heightPrev - yWindow

   -- Calcul du ratio du senseur
   local ratioSensor
   if( up ~= "X" ) then
      ratioSensor = math.tan( halfAngleOnY ) / math.tan( halfAngleOnX )
   else
      ratioSensor = math.tan( halfAngleOnX ) / math.tan( halfAngleOnY )
   end

   -- Ajustement de la taille de la fenêtre
   local height = math.ceil( width / ratioSensor - 1e-4 )
   celestia:setwindowinfos( xPos, yPos, width + xDeco, height + yDeco )

   -- Mémorisation de la taille intérieure de l'écran (pour Cosmographia)
   rt.width = width
   rt.height = height

   -- Appel de la fonction standard pour le senseur
   setCameraSensorView( sensorFullName, halfAngleOnX, halfAngleOnY, up, 0 )

end


--------------------------------------------------------------------------------
-- setCameraSynchronous
--
-- Caméra générique attachée à un repère donné.
--
-- objName : nom Celestia complet du satellte
-- refObjectName : nom de l'objet repère de référence auquel s'attacher
--                 Exemple : Sol/Earth/CubeSat_ref/CubeSat_Eme2000Axes
-- direction : direction depuis laquelle observer l'objet (X, -X, Y, etc.)
-- distanceFactor : Facteur de distance vis à vis de la distance par défaut
--------------------------------------------------------------------------------

function setCameraSynchronous( objName, refObjectName, direction, distanceFactor )

   local camera = celestia:getobserver()

   -- Recherche et sélection du repère de référence
   local refObjectSelect = celestia:find( refObjectName )
   if( refObjectSelect:type() == "null" ) then
      return
   end
   celestia:select( refObjectSelect )

   -- On retient le nom de l'objet sélectionné
   local objectSelect = celestia:find( objName )
   if( objectSelect:type() == "null" ) then
      return
   end

   -- Distance camera-objectSatellite
   local objectradius = objectSelect:radius()
   local distanceFactorBase = 30000
   if( objectSelect:type() ~= "planet" and objectSelect:type() ~= "star" ) then
      local vtsSat = getVTSSatellite( objName )
      if ( vtsSat ~= nil ) then
         objectradius = vtsSat.magCoeff * vtsSat.maxRadius
         distanceFactorBase = 5000
      end
   end
   distanceToObject = objectradius * distanceFactorBase * distanceFactor / uly2m

   -- Synchronisation de la position de la caméra avec le repère
   local frame = celestia:newframe( "bodyfixed", refObjectSelect )
   camera:setframe( frame )

   -- Définition de la position de la caméra
   local dirVector
   local upVector
   if( direction == "+X" ) then
      dirVector = celestia:newvector( -1, 0, 0 )
      upVector = celestia:newvector( 0, 0, -1 )
   elseif( direction == "+Y" ) then
      dirVector = celestia:newvector( 0, 1, 0 )
      upVector = celestia:newvector( -1, 0, 0 )
   elseif( direction == "+Z" ) then
      dirVector = celestia:newvector( 0, 0, -1 )
      upVector = celestia:newvector( 0, 1, 0 )
   elseif( direction == "-X" ) then
      dirVector = celestia:newvector( 1, 0, 0 )
      upVector = celestia:newvector( 0, 0, 1 )
   elseif( direction == "-Y" ) then
      dirVector = celestia:newvector( 0, -1, 0 )
      upVector = celestia:newvector( 1, 0, 0 )
   elseif( direction == "-Z" ) then
      dirVector = celestia:newvector( 0, 0, 1 )
      upVector = celestia:newvector( 0, -1, 0 )
   elseif( direction == "XYZ" ) then
      dirVector = celestia:newvector( -1, 1, -1 )
      upVector = celestia:newvector( 0, 0, -1 )
   elseif( direction == "YZX" ) then
      dirVector = celestia:newvector( -1, 1, -1 )
      upVector = celestia:newvector( -1, 0, 0 )
   end

   -- Positionnement de la caméra
   setCameraPositionAndDirection( refObjectSelect, dirVector, upVector, distanceToObject )

   -- On retient le nom de l'objet sélectionné
   local satObjectSelect = celestia:find( objName )
   lastSelectedObject = satObjectSelect

end


--------------------------------------------------------------------------------
-- setCameraCenter
--
-- Caméra centrée sur l'objet
--------------------------------------------------------------------------------

function setCameraCenter( objectName )

   local obs = celestia:getobserver()

   -- Annulation d'un center déjà en cours et fin de fonction
   if( obs:travelling() ) then
      obs:cancelgoto()
      return
   end

   -- Sélection de l'objet
   local object = celestia:find( objectName )
   if( object:type() == "null" ) then
      return
   end

   celestia:select( object )
   -- Centrage de l'objet
   obs:center( object, 1 )
end


--------------------------------------------------------------------------------
-- setCameraGoto
--
-- Caméra se déplace jusqu'à l'objet
--------------------------------------------------------------------------------

function setCameraGoto( objectName )

   local obs = celestia:getobserver()

   -- Annulation d'un goto déjà en cours et fin de fonction
   if( obs:travelling() ) then
      obs:cancelgoto()
      return
   end

   local object = celestia:find( objectName )
   if( object:type() == "null" ) then
      return
   end
   -- Sélection de l'objet
   celestia:select( object )

   -- Si c'est un satellite VTS on prend en compte le rayon max pour le goto
   -- Le goto essaye de remplir au maximum la fenêtre de celestia avec l'objet
   local fov = obs:getfov()
   local boundingRadius
   if( object:type() == "planet" ) then
      boundingRadius = object:radius()
   else
      local vtsSat = getVTSSatellite( objectName )
      if ( vtsSat ~= nil ) then
         boundingRadius = vtsSat.magCoeff * vtsSat.maxRadius
      else
         boundingRadius = object:radius()
      end
   end
   obs:gotodistance( object, 5.5 *  boundingRadius / (fov / 0.4688), 1 )
end


--------------------------------------------------------------------------------
-- setCameraGotoFrom
--
-- Paramètres de début du tracking
--------------------------------------------------------------------------------

function setCameraGotoFrom()

   local obs = celestia:getobserver()

   -- Annulation d'un goto déjà en cours
   obs:cancelgoto()

   local actual_frame = obs:getframe()
   trackingParameters.from = actual_frame:to(obs:getposition())
   trackingParameters.initialOrientation = actual_frame:to(obs:getorientation())

   -- Sauvegarde de la caméra initiale toString
   trackingParameters.initialToString = getCameraToString()

   -- Step effectué
   trackingParameters.step1complete = true

   celestia:flash( "Tracking source position set" )
end


--------------------------------------------------------------------------------
-- setCameraGotoTo
--
-- Paramètres de fin du tracking
--------------------------------------------------------------------------------

function setCameraGotoTo()

   local obs = celestia:getobserver()

   -- Annulation d'un goto déjà en cours
   obs:cancelgoto()

   local actual_frame = obs:getframe()
   trackingParameters.to = actual_frame:to(obs:getposition())
   trackingParameters.finalOrientation = actual_frame:to(obs:getorientation())

   -- Step effectué
   trackingParameters.step2complete = true

   celestia:flash( "Tracking target position set" )
end


--------------------------------------------------------------------------------
-- setCameraGotoSave
--
-- Sauvegarde du tracking dans la table de paramètres
--------------------------------------------------------------------------------

function setCameraGotoSave( duration, startInterpolation, endInterpolation, accelTime )

   local obs = celestia:getobserver()

   -- Annulation d'un goto déjà en cours 
   obs:cancelgoto()

   if( trackingParameters.step1complete == false or
       trackingParameters.step2complete == false ) then
      celestia:flash( "Missing tracking configuration step" )
      return
   end

   trackingParameters.duration = duration
   trackingParameters.startInterpolation = startInterpolation
   trackingParameters.endInterpolation = endInterpolation
   trackingParameters.accelTime = accelTime

   -- Sauvegarde des paramètres du tracking
   local cam = string.format( "%.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f %.15f",
                              trackingParameters.duration,
                              trackingParameters.startInterpolation,
                              trackingParameters.endInterpolation,
                              trackingParameters.accelTime,
                              trackingParameters.from:getx(),
                              trackingParameters.from:gety(),
                              trackingParameters.from:getz(),
                              trackingParameters.initialOrientation:real(),
                              trackingParameters.initialOrientation:imag():getx(),
                              trackingParameters.initialOrientation:imag():gety(),
                              trackingParameters.initialOrientation:imag():getz(),
                              trackingParameters.to:getx(),
                              trackingParameters.to:gety(),
                              trackingParameters.to:getz(),
                              trackingParameters.finalOrientation:real(),
                              trackingParameters.finalOrientation:imag():getx(),
                              trackingParameters.finalOrientation:imag():gety(),
                              trackingParameters.finalOrientation:imag():getz()
                              )
   trackingParameters.trackingToString = cam

   -- Step effectué (peut être invalide si les reference frame de l'observer sont différents)
   trackingParameters.step3complete = true
end


--------------------------------------------------------------------------------
-- setCameraGotoLiveRun
--
-- Exécution du tracking
--------------------------------------------------------------------------------

function setCameraGotoLiveRun()

   local obs = celestia:getobserver()

   -- Annulation d'un goto déjà en cours 
   obs:cancelgoto()

   -- Un step manquant et on quitte
   if( trackingParameters.step1complete == false or
       trackingParameters.step2complete == false or
       trackingParameters.step3complete == false ) then
      celestia:flash( "Missing tracking configuration step" )
      return
   end

   -- Sauvegarde autorisée
   trackingParameters.canBeSaved = true

   -- Déroulement du tracking
   obs:gototablekeepframe(trackingParameters)
end


--------------------------------------------------------------------------------
-- setCameraGotoClear
--
-- Effacement du tracking
--------------------------------------------------------------------------------

function setCameraGotoClear()

   local obs = celestia:getobserver()

   -- Annulation d'un goto déjà en cours
   obs:cancelgoto()

   -- Effacement du tracking
   trackingParameters.step1complete = false
   trackingParameters.step2complete = false
   trackingParameters.step3complete = false
   trackingParameters.canBeSaved = false
   
   celestia:flash( "Tracking parameters cleared" )
end


--------------------------------------------------------------------------------
-- setCameraBodyToBody
--
-- Caméra dans l'axe d'un corps aligné avec un autre corps
--------------------------------------------------------------------------------

function setCameraBodyToBody( direction, satelliteName, bodyName )

   -- direction Backward par défaut
   local cameraDirection = 1
   if( direction == "Forward" ) then
      cameraDirection = -1
   end

   -- Récupération des objets
   if( bodyName == "SELFCENTRALBODY" ) then
      -- Si le body est le corps central du satellite
      local vtsSat = getVTSSatellite( satelliteName )
      objectBody = celestia:find( vtsSat.centralBodyName )
      if( objectBody:type() == "null" ) then
         return
      end
   else
      -- Corps quelconque
      objectBody = celestia:find( bodyName )
      if( objectBody:type() == "null" ) then
         return
      end
   end

   objectRefSatellite = celestia:find( satelliteName .. "_ref" )
   if( objectRefSatellite:type() == "null" ) then
      return
   end
   objectSatellite = celestia:find( satelliteName )
   if( objectRefSatellite:type() == "null" ) then
      return
   end
   camera = celestia:getobserver()

   -- Distance camera-objectSatellite
   distanceToObject = objectSatellite:radius() * 30000 / uly2m

   -- Sélection de l'objet proche
   celestia:select( objectSatellite )

   -- On retient le nom de l'objet sélectionné pour la fonction Home
   lastSelectedObject = objectSatellite

   -- Mise à jour de la position des objets. Devrait être dans le tick() si on veut une caméra satellite-satellite.
   satPosition = objectRefSatellite:getposition()
   bodyPosition = objectBody:getposition()

   -- Test du satellite centre body
   if( satPosition:getx() == bodyPosition:getx()
   and satPosition:gety() == bodyPosition:gety()
   and satPosition:getz() == bodyPosition:getz() ) then
      objectToObjectVector = celestia:newvector( 1, 0, 0 )

      -- Caméra verrouillée sur le satellite (équivalent synchronous)
      frame = celestia:newframe("planetographic", objectRefSatellite)
      camera:setframe( frame )

   else
      -- Vecteur objectRefSatellite-objectBody
      objectToObjectVector = satPosition:vectorto( bodyPosition )
      objectToObjectVector = objectToObjectVector:normalize()

      -- Caméra verrouillée sur le corps central
      frame = celestia:newframe("lock", objectRefSatellite, objectBody)
      camera:setframe( frame )

   end

   -- Mise à jour de la position de la caméra
   cameraPos = celestia:newposition( cameraDirection * distanceToObject * objectToObjectVector:getx() + satPosition:getx(),
                                     cameraDirection * distanceToObject * objectToObjectVector:gety() + satPosition:gety(),
                                     cameraDirection * distanceToObject * objectToObjectVector:getz() + satPosition:getz() )
   camera:setposition( cameraPos )
   -- Direction de visée de la caméra
   camera:lookat(cameraPos, satPosition , celestia:newvector(0,0,1))
end


--------------------------------------------------------------------------------
-- setCameraOrbit
--
-- Caméra de visualisation d'orbite
--------------------------------------------------------------------------------

function setCameraOrbit( satelliteName, opposite )

   -- Récupération des objets
   camera = celestia:getobserver()

   -- Récupération de la structure du satellite en global pour setCameraOrbit()
   gCurrVTSSatellite = getVTSSatellite( satelliteName )

   -- Pointeur sur le référentiel du satellite
   local currSatRef = gCurrVTSSatellite.nodes[1].object

   -- Corps central associé au satellite
   local centralBody = celestia:find( string.gsub( gCurrVTSSatellite.centralBodyName, ".*/", "" ) .. "_Eme2000Axes" )
   if( centralBody:type() == "null" ) then
      return
   end

   -- Direction de la caméra :  1 ou -1 pour se placer de l'autre côté de la planète
   if( opposite ) then
      cameraDirection = -1
   else
      cameraDirection = 1
   end

   -- Distance camera-planet à 10 fois l'altitude du satellite
   local distanceToPlanet = currSatRef:getposition():vectorto(centralBody:getposition()):length() * uly2m * 10
   local dto = cameraDirection * distanceToPlanet / uly2m

   -- Sélection du satellite
   objectToSelect = celestia:find( satelliteName )
   if( centralBody:type() == "null" ) then
      celestia:log( "Can't select " ..objectToSelect )
   end
   celestia:select( objectToSelect )

   -- Affichage des orbites (paramètre satellite pas trouvé dans les orbitflags)
   renderFlags = {} -- create table
   renderFlags.orbits = true
   celestia:setrenderflags(renderFlags)

   -- On crée un repère planète
   bodyFixedFrame = celestia:newframe( "bodyfixed", centralBody )

   -- Caméra centrée sur la planète (caméra inertielle)
   camera:setframe(bodyFixedFrame)

   -- Position planète
   bodyPos = centralBody:getposition()

   -- Calcul du vecteur up dans le système de coordonnées de Celestia
   universalUp = bodyFixedFrame:from( celestia:newrotation( 1, 0, 0, 0 ) ):transform( celestia:newvector(0,0,-1) )

   -- Position satellite dans le repère planète
   satPos = bodyFixedFrame:to( currSatRef:getposition() )

   -- Vecteur satellite->planète
   planetVect = celestia:newvector( satPos:getx(), satPos:gety(), satPos:getz() )
   planetVect = planetVect:normalize()

   -- Deuxième vecteur satellite->planète
   satVel = currSatRef:getvelocity() - centralBody:getvelocity() -- Vitesse exprimée dans le repère interne de Celestia
   satVelPosUniv = celestia:newposition( satVel:getx(), satVel:gety(), satVel:getz() ) ;
   satVelPos = bodyFixedFrame:to( satVelPosUniv )
   planetVect2 = celestia:newvector( satVelPos:getx(), satVelPos:gety(), satVelPos:getz() )
   planetVect2 = planetVect2:normalize()

   -- Produit vectoriel des deux vecteurs satellite planète pour se placer à la perpendiculaire de la trajectoire
   posVect = crossProduct(planetVect,planetVect2)
   posVect = posVect:normalize()
   pos = celestia:newposition( dto*posVect:getx(), dto*posVect:gety(), dto*posVect:getz() )

   -- Position de la caméra
   camera:setposition( bodyFixedFrame:from( pos ) )
   camera:lookat( bodyPos , universalUp )

end


--------------------------------------------------------------------------------
-- setCameraHome
-- Affiche l'objet demandé
--------------------------------------------------------------------------------

function setCameraHome( homeObject )

   lastSelectedObject = homeObject

   if( homeObject == nil ) then
      homeObject = celestia:find( "Earth" )
   end

   celestia:select(homeObject)

   -- Arrêt du hook controllant la camera depuis android
   boolHookCodeAndroid = false

   -- Demande de réinit de la camera
   aCameraInit = true

   -- On se met à 10 fois le rayon de l'objet
   aCamera:gotodistance( homeObject, homeObject:radius()*10, 1.0 )
end


--------------------------------------------------------------------------------
-- initCameraAndroid
--
-- Initialisation d'objets GLOBAUX appelés souvent. Appel à ne pas supprimer
-- sinon les fonctions utilisant ces objets ne marcheront plus.
--------------------------------------------------------------------------------

function initCameraAndroid()

   -- caméra dans repère satellite
   aCamera = celestia:getobserver()

   -- Demande de l'init
   aCameraInit = true
   -- Caméra non active
   boolHookCodeAndroid = false
end


--------------------------------------------------------------------------------
-- initSimulation
--
-- Initialisation des structures globales pour la simulation
--------------------------------------------------------------------------------

function initSimulation()

   -- Tableau global des satellites
   gSatellites = {}

   -- Tableau global des corps centraux
   gBodies = {}

   -- Tableau global des ROI
   gROI = {}
   gRoiCount = 0
end


--------------------------------------------------------------------------------
-- initBody
--
-- Initialisation des structures globales pour la simulation
--------------------------------------------------------------------------------

function initBody( bodyName )

   -- Ajout d'un body à la liste globale
   local indexBody = #gBodies + 1

   -- Création de la structure body
   gBodies[indexBody] = {}

   -- Stockage des informations
   local bodyObject = celestia:find( bodyName )
   if( bodyObject:type() == "null" ) then
      return
   end
   gBodies[indexBody].object = bodyObject
   -- Récupération du nom court
   gBodies[indexBody].name = bodyObject:name()
   -- Stockage du rayon original
   gBodies[indexBody].radius = bodyObject:radius()

   -- Préchargement des textures du corps
   bodyObject:preloadtexture()
end


--------------------------------------------------------------------------------
-- initSatellite
--
-- Initialisation d'un satellite. Parcourt ses sous objets et calcule son
-- rayon maximal
--------------------------------------------------------------------------------

function initSatellite( satName, parentPath )

   -- Ajout d'un satellite à la liste globale
   local indexSat = #gSatellites + 1

   -- Création de la structure satellite
   gSatellites[indexSat] = {}

   -- Satellite courant, variable globale pour accès en écriture dans
   -- la fonction storeRadiusAndWalkChildren
   gCurrentSat = {}
   gCurrentSat.name = satName
   gCurrentSat.centralBodyName = parentPath

   -- Stockage de l'arbre du satellite (il est nécessaire de faire le stockage
   -- avant l'appel à storeRadiusAndWalkChildren)
   gSatellites[indexSat] = gCurrentSat

   -- Sous objets du satellite
   gCurrentSat.nodes = {}

   -- L'objet racine est le référenciel
   local rootObject = getObjectFromFullName( parentPath .. "/" .. satName, true )
   if( rootObject:type() == "null" ) then
      return
   end

   -- Parcours du satellite récursif pour stocker les rayons des sous objets
   storeRadiusAndWalkChildren( rootObject )

   -- Recherche du plus gros sous objet du satellite
   gCurrentSat.maxRadius = rootObject:radius()
   for k, child in pairs(gCurrentSat.nodes) do

      -- Calcul du max
      if( child.object:radius() > gCurrentSat.maxRadius ) then
         gCurrentSat.maxRadius = child.object:radius()
      end
   end

   -- Facteur de grossissement par défaut
   gCurrentSat.magCoeff = 1
end


-- Fonction utilitaire
-- Stockage du rayon d'un noeud et parcours des enfants
function storeRadiusAndWalkChildren( node )

   -- Index du noeud courant
   local nbNode = #gCurrentSat.nodes + 1

   -- Stockage dans un noeud de l'objet celestia et de son rayon d'origine
   gCurrentSat.nodes[nbNode] = CelObject:new{ object = node, radius = node:radius() }

   -- Appel récursif pour chaque enfant
   childrenList = node:getchildren()
   for i, child in pairs(childrenList) do

      -- Détection du suffixe _sens_ref pour ignorer les senseurs
      local sensRef = string.find( child:name(), "_sens_ref" )

      if( sensRef == nil ) then
         storeRadiusAndWalkChildren( child )
      end
   end
end


--------------------------------------------------------------------------------
-- magnifySatellite
--
-- Commande de grossissement du satellite
-- magCoeff entre 1 et 100
--------------------------------------------------------------------------------

function magnifySatellite( satelliteName, magCoeff )

   for i, satStruct in pairs(gSatellites) do
      if( satelliteName == satStruct.name ) then

         -- Stockage du coeff à la racine du satellite
         satStruct.magCoeff = magCoeff

         -- Parcours des sous objets
         for j, child in pairs(satStruct.nodes) do
            -- Application du grossissement à toute l'arborescence du satellite,
            -- même le _ref pour grossir la boîte englobante permettant un affichage
            -- correct des labels
            child.object:setmagcoeff( satStruct.magCoeff * child.radius, satStruct.magCoeff ) ;
         end
      end
   end
end


-- Fonction utilitaire
-- Redimensionnement du corps central par rapport aux satellites
function adjustCentralBody()

   -- Corps central
   local centralBody = celestia:find( gCentralBodyName )
   if( centralBody:type() == "null" ) then
      return
   end

   -- Corps central
   local centralPos = centralBody:getposition()
   local centralRadius = gCentralBodyRadius * gCentralBodyMagCoeff

   -- Recherche du satellite étant le plus proche du corps central (en termes
   -- de distance pernant en compte les tailles virtuelles des objets
   local firstLoop = true
   local nearestSatRadius = 0
   local nearestSatDistance = 0
   for i, satStruct in pairs(gSatellites) do
      -- Position du parent (_ref)
      local satPos = satStruct.nodes[1].object:getposition()
      -- Rayon max du satellite stocké à la racine en km
      local satRadius = satStruct.magCoeff * satStruct.maxRadius

      -- Distance entre le satellite et le corps central
      local distance = math.sqrt( math.pow( satPos.x * ulyToKm - centralPos.x * ulyToKm, 2 ) +
                                  math.pow( satPos.y * ulyToKm - centralPos.y * ulyToKm, 2 ) +
                                  math.pow( satPos.z * ulyToKm - centralPos.z * ulyToKm, 2 ) )

      -- Test du satellite le plus proche
      if(((distance - satRadius) < (nearestSatDistance - nearestSatRadius)) or firstLoop ) then
         nearestSatDistance = distance
         nearestSatRadius = satRadius
         firstLoop = false
      end
   end

   -- Rayon du corps central proportionnel à la distance du satellite
   gCentralBodyMagCoeff = ( nearestSatDistance - nearestSatRadius ) / gCentralBodyRadius

   -- Le coefficient de grossissement ne peut pas être > 1 ou < 0
   if( gCentralBodyMagCoeff > 1 ) then
      gCentralBodyMagCoeff = 1
   elseif( gCentralBodyMagCoeff < 0 ) then
      gCentralBodyMagCoeff = 0.0001
   end
   -- Affectation du nouveau rayon au corps central
   centralBody:setradius( gCentralBodyRadius * gCentralBodyMagCoeff )
end

----------------------------------------------
-- Define utils functions
----------------------------------------------
getRadius = function(obj_t)
    local radius_t = {};
    for k, obj in pairs(obj_t) do
        radius_t[k] = obj:radius();
    end
    return radius_t;
end

getSolChildrenFromType = function(magType)
    local magChildren = {};
    local allChildren = magSol:getchildren();
    for k, child in pairs(allChildren) do
        if child:type() == magType then
            magChildren[k] = CelObject:new{ object = child, radius = child:radius() } ;
        end
    end
    return magChildren;
end


--------------------------------------------------------------------------------
-- initStandardBodies
--
-- Sauvegarde des tailles des corps céleste avant grossissement de
-- setSolarMagnification()
--------------------------------------------------------------------------------

function initStandardBodies()

   -- Planètes forcées en dur
   magnified_objects = "planets"

   magSol = celestia:find("Sol");
   magEarth = celestia:find("Sol/Earth");
   magMoon = celestia:find("Sol/Earth/Moon");

   -- Get magnification elements
   gMagObjects = getSolChildrenFromType("planet");
end


--------------------------------------------------------------------------------
-- disableAtmospheresIfNeeded
--
-- Désactivation des atmosphères si un corps est zoomé
--------------------------------------------------------------------------------

function disableAtmospheresIfNeeded( bodyMagCoeff )

   local t = {} ;
   if( atmospheresWereHere == "unset" ) then
      if( tonumber(bodyMagCoeff) > 1 ) then

         -- Save
         t = celestia:getrenderflags()
         if( t.atmospheres == true ) then
            atmospheresWereHere = "yes"
         else
            atmospheresWereHere = "no"
         end
         t.atmospheres = false ;
         celestia:setrenderflags(t)

      end
   else
      if( tonumber(bodyMagCoeff) <= 1 ) then

         -- Restore
         if( atmospheresWereHere == "yes" ) then
            t.atmospheres = true ;
            celestia:setrenderflags(t)
         end
         atmospheresWereHere = "unset"

      end
   end

end


--------------------------------------------------------------------------------
-- setSolarMagnification
--
-- Grossissement de toutes les planètes du système solaire
--------------------------------------------------------------------------------

setSolarMagnification = function( bodyMagCoeff )

   -- Magnify objects (increase the size of objects).
   for k, magObj in pairs(gMagObjects) do
      magObj.object:setradius(magObj.radius * bodyMagCoeff)
   end

   -- Disable atmospheres
   disableAtmospheresIfNeeded( bodyMagCoeff )

   -- Move the observer outside of the selected object.
   local sel = celestia:getselection();
   if not(empty(sel)) and sel:type() == "planet" then
      local obs = celestia:getobserver();
      local sel = celestia:getselection();
      local mag_distfromsel = sel:getposition():distanceto(obs:getposition())
      local mag_sel_radius = sel:radius();
      if mag_distfromsel < mag_sel_radius then
          local fov = obs:getfov();
          obs:gotodistance(sel, 5.5 * sel:radius() / (fov / 0.4688), 0.01)
      end
   end
end


--------------------------------------------------------------------------------
-- magnifyBody
--
-- Grossissement d'un corps celeste
--------------------------------------------------------------------------------

magnifyBody = function( bodyName, bodyCoeff )

   -- Récupération du body VTS et son rayon original
   local vtsBody = getVTSBody( bodyName )
   vtsBody.object:setradius( vtsBody.radius * bodyCoeff )

   -- Disable atmospheres
   disableAtmospheresIfNeeded( bodyCoeff )

end


--------------------------------------------------------------------------------
-- createMultiView
--
-- Création d'un ensemble d'observers
--
-- Ordre des observers 2 4 :
--    5 6 7 8
--    1 2 3 4
--
-- nbHoriz : nombre de lignes
-- nbVert : nombre de colonnes
--------------------------------------------------------------------------------

function createMultiView( nbHoriz, nbVert )

   -- Fermeture de toutes les vues
   celestia:getobserver():singleview()

   -- Création des vues horizontales
   for i=1, nbVert-1 do
      observers = celestia:getobservers()
      observers[i]:splitview("V", 1/(nbVert-i+1) )
   end

   -- Création des vues verticales
   for i=1, nbHoriz-1 do
      observers = celestia:getobservers()
      for j=1+(i-1)*nbVert, nbVert+(i-1)*nbVert do
         observers[j]:splitview("H", 1/(nbHoriz-i+1) )
      end
   end

   -- Oubli des caméras des vues fermées
   for i = nbHoriz*nbVert + 1, #rt.lastReceivedCamera do
      table.remove( rt.lastReceivedCamera, i )
   end

   -- Enregistrement du layout
   rt.multi.h = nbHoriz
   rt.multi.v = nbVert
end


--------------------------------------------------------------------------------
-- getObserverIndex
--
-- Retourne l'index d'un observer à partir de ses coordonnées
--
-- Pour un layout 2x4, l'index est défini comme suit :
--    1x1 1x2 1x3 1x4    =>    5 6 7 8
--    2x1 2x2 2x3 2x4    =>    1 2 3 4
--------------------------------------------------------------------------------

function getObserverIndex( row, column )
   return rt.multi.v * (rt.multi.h - tonumber(row)) + tonumber(column)
end


--------------------------------------------------------------------------------
-- setFOV
--
-- Modification du FOV.
--
-- newFov : FOV en degrés
--------------------------------------------------------------------------------

function setFov( newFov )
   local obs = celestia:getobserver()
   obs:setfov( math.rad( tonumber(newFov) ) )
end


--------------------------------------------------------------------------------
-- captureAndStreamBuffer
--
-- Capture du buffer image ou de profondeur et renvoi vers VTS
--------------------------------------------------------------------------------

function captureAndStreamBuffer( imageType, doForward, destFwdId )

         -- Initialisations
         local success = false
         local imageBase64 = nil
         local width = 0
         local height = 0
         local cmdToSend = "DATA 0 "

         -- Type de capture
         if( imageType == "Image" ) then
            -- Capture d'une image
            success, width, height, imageBase64 = celestia:capturebuffertostring( "image" )
            cmdToSend = cmdToSend .. "Image "

         elseif( imageType == "Depth" ) then
            -- Capture du Z-buffer
            success, width, height, imageBase64 = celestia:capturebuffertostring( "depth" )
            cmdToSend = cmdToSend .. "Depth "

         else
            -- Erreur d'argument
            celestia:log( "Unknown capture buffer type : " .. imageType )
            return
         end

         -- Renvoi de l'image capturée
         if( success == true and imageBase64 ~= nil ) then

            -- Construction de la commande
            cmdToSend = cmdToSend .. imageBase64 .. "\n"

            -- Traitement de la demande de forward
            if( doForward ) then
               cmdToSend = "FWD " .. destFwdId .. " " .. cmdToSend .. "\n"
            end

            -- Timeout de 10 secondes pour le transfert
            rt.client:settimeout( 10, 'b' )
            local b,err = rt.client:send( cmdToSend )
            rt.client:settimeout( 0, 'b' )
         else
            celestia:log( "Error capturing buffer" )
         end

end



--------------------------------- End Of File ----------------------------------
