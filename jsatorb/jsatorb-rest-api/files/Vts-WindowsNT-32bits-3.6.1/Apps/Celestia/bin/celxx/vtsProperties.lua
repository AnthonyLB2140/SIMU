--------------------------------------------------------------------------------
-- vtsProperties.lua
--
-- Copyright © (2020) CNES All rights reserved
--
-- VER : $Id: vtsProperties.lua 9026 2021-12-13 14:31:13Z jee $
--------------------------------------------------------------------------------



--------------------------------------------------------------------------------
-- getObjectFromFullName
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- return : objet Celestia
--------------------------------------------------------------------------------

function getObjectFromFullName( satelliteFullName, askedRef )

   local celObject = nil
   local refObject = nil
   local celestiaFullName = ""
   local suggestedFullName = ""

   -- Split de la ligne en fonction des slashes
   for word in string.gmatch( satelliteFullName, "([^/]+)" ) do

      celObject = nil
      if( string.len( celestiaFullName ) == 0 ) then
         -- Cas Sol/
         celestiaFullName = word
         suggestedFullName = celestiaFullName
      else
         -- Cas Sol/Earth ou Sol/Earth/CubeSat
         suggestedFullName = celestiaFullName .. "/" .. word
      end

      celObject = celestia:find( suggestedFullName )

      if( not(empty(celObject)) and celObject:type() ~= "location" ) then
         -- Sol/Earth
         celestiaFullName = suggestedFullName
         refObject = celObject
      else
         -- Sol/Earth/CubeSat
         suggestedFullName = celestiaFullName .. "/" .. word .. "_ref/" .. word
         suggestedRefName = celestiaFullName .. "/" .. word .. "_ref"
         celObject = celestia:find( suggestedFullName )
         refObject = celestia:find( suggestedRefName )
         if( not(empty(celObject)) ) then
            -- Sol/Earth/CubeSat_ref/CubeSat
            celestiaFullName = suggestedFullName
         else
            -- Sol/Earth/CubeSat_ref/CubeSat/Sensor_ref/Sensor
            suggestedFullName = celestiaFullName .. "/" .. word .. "_sens_ref/" .. word
            suggestedRefName = celestiaFullName .. "/" .. word .. "_sens_ref"
            celObject = celestia:find( suggestedFullName )
            refObject = celestia:find( suggestedRefName )
            if( not(empty(celObject)) ) then
               celestiaFullName = suggestedFullName
            else
               celestia:log( "VTS error: " .. satelliteFullName .. " not found!" )
               celestiaFullName = ""
            end
         end
      end
   end

   -- Retour de l'objet référentiel
   if( askedRef == true ) then
      return refObject
   end
   -- retour de l'objet Celestia
   return celObject
end


--------------------------------------------------------------------------------
-- getNamedChild
--
-- parentObject : objet Celestia parent
-- childName : nom du fils à chercher
-- return : objet fils ou nil
--------------------------------------------------------------------------------

function getNamedChild( parentObject, childName )
   for k, child in pairs(parentObject:getchildren()) do
      if child:name() == childName then
         return child
      end
   end
   return nil
end


--------------------------------------------------------------------------------
-- getObjectNameFromFullName
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- return : nom de l'objet
--------------------------------------------------------------------------------

function getObjectNameFromFullName( satelliteFullName )
   local slash = string.match(satelliteFullName, '.*()'.."/")

   if( slash ~= nil ) then
      return satelliteFullName:sub( slash+1, satelliteFullName:len() )
   else
      return satelliteFullName
   end
end


--------------------------------------------------------------------------------
-- getParentObjectNameFromFullName
--
-- satelliteFullName : chemin de l'objet parent au format conventionnel
-- return : nom de l'objet
--------------------------------------------------------------------------------

function getParentObjectNameFromFullName( objectFullName )
   local slash = string.match(objectFullName, '.*()'.."/")

   if( slash ~= nil and slash > 1 ) then
      return objectFullName:sub( 1, slash - 1 )
   else
      return objectFullName
   end
end


--------------------------------------------------------------------------------
-- setPlanetographicGridVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setPlanetographicGridVisible( bodyFullName, isVisible )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )

   -- Visibilité
   if( isVisible == true ) then
      visiObject:addreferencemark{ type = "planetographic grid" }
   else
      visiObject:removereferencemark("planetographic grid")
   end
end


--------------------------------------------------------------------------------
-- setTerminatorVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setTerminatorVisible( bodyFullName, isVisible )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )
   local sunObject = celestia:find( "Sol" )

   -- Visibilité
   if( isVisible == true ) then
      visiObject:addreferencemark{ type = "terminator" }
      visiObject:addreferencemark{type = "visible region", size = 1000, color = "yellow",
                      opacity = 1.0, tag = "SunTerminator", target = sunObject}
   else
      visiObject:removereferencemark("SunTerminator")
   end
end


--------------------------------------------------------------------------------
-- setOrbitVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setOrbitVisible( satelliteFullName, isVisible )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( satelliteFullName, true )

   -- Visibilité
   if( isVisible == true ) then
      visiObject:setorbitvisibility( "always" )
   else
      visiObject:setorbitvisibility( "never" )
   end
end


--------------------------------------------------------------------------------
-- setOrbitWindow
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- windowBeginDuration : Durée de trace derrière le satellite en heures
-- windowEndDuration : Durée de trace devantle satellite en heures
--------------------------------------------------------------------------------

function setOrbitWindow( satelliteFullName, windowBeginDuration, windowEndDuration )

   -- Récupération du ref de l'objet
   local object = getObjectFromFullName( satelliteFullName, true )

   -- Longueur de la trace d'orbite en jours
   local duration = windowBeginDuration + windowEndDuration
   object:setorbitlength( duration / 24, windowEndDuration / 24 )
end


--------------------------------------------------------------------------------
-- setEme2000AxesVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setEme2000AxesVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_Axis
   local visiObject = getNamedChild( refObject, satName .. "_Eme2000Axes" )

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setQswAxesVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setQswAxesVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_Axis
   local visiObject = getNamedChild( refObject, satName .. "_QswAxes" )

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setTnwAxesVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setTnwAxesVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_Axis
   local visiObject = getNamedChild( refObject, satName .. "_TnwAxes" )

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setFrameAxesVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setFrameAxesVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_Axis
   local visiObject = getNamedChild( refObject, satName .. "_Axes" )

   -- Si l'objet n'est pas trouvé on sort
   if ( visiObject == nil  ) then
      return
   end

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setSunDirectionVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setSunDirectionVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_SunDir
   local visiObject = getNamedChild( refObject, satName .. "_SunDir" )

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setBodyDirectionVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setBodyDirectionVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_BodyDir
   local visiObject = getNamedChild( refObject, satName .. "_BodyDir" )

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setVelocityVectorVisible
--
-- satelliteFullName : chemin du satellite au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setVelocityVectorVisible( satelliteFullName, isVisible )

   -- Récupération du nom du satellite
   local satName = getObjectNameFromFullName( satelliteFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( satelliteFullName, true )

   -- Recherche de <satName>_ref/<satName>_VelDir
   local visiObject = getNamedChild( refObject, satName .. "_VelDir" )

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- findVisualizer
--------------------------------------------------------------------------------

function findVisualizer( visualizerName )
   -- Parcours de tous les visualizers 
   for visualizerIndex, visualizer in ipairs(visualizers) do
      if( visualizerName == visualizer.tag ) then
         return visualizer ;
      end
   end
   return nil
end


--------------------------------------------------------------------------------
-- setVisualizerVisible
--
-- visualizerFullName : chemin du visualizer au format conventionnel
--------------------------------------------------------------------------------

function setVisualizerVisible( visualizerFullName, isVisible )

   -- Récupération des infos de vtsConfig.celx
   local visualizerInfo = findVisualizer( visualizerFullName )
   if( visualizerInfo == nil ) then 
      return
   end

   -- Récupération du ref du frame du visualizer
   local frameObject = getObjectFromFullName( visualizerInfo.parent )
   if( frameObject == nil ) then 
      return
   end

   -- Commande
   if( isVisible ) then
       frameObject:addreferencemark( visualizerInfo )
    else
       frameObject:removereferencemark( visualizerFullName )
   end
end

--------------------------------------------------------------------------------
-- setVisualizerColor
--
-- visualizerFullName : chemin du visualizer au format conventionnel
-- color : couleur du visualizer
--------------------------------------------------------------------------------

function setVisualizerColor( visualizerFullName, color )

   -- Récupération des infos de vtsConfig.celx
   local visualizerInfo = findVisualizer( visualizerFullName )
   if( visualizerInfo == nil ) then 
      return
   end
   
   -- Sauvegarde dans le modèle de données lua
   visualizerInfo.color = color

   -- Récupération du ref du frame du visualizer
   local frameObject = getObjectFromFullName( visualizerFullName .. "_ref" )
   if( frameObject == nil ) then 
      return
   end

   -- Couleur
   frameObject:setvisualizercolor( visualizerFullName, color )

end


--------------------------------------------------------------------------------
-- setVisualizerScale
--
-- visualizerFullName : chemin du visualizer au format conventionnel
-- scale : facteur d'échelle du visualizer
--------------------------------------------------------------------------------

function setVisualizerScale( visualizerFullName, scale )

   -- Récupération des infos de vtsConfig.celx
   local visualizerInfo = findVisualizer( visualizerFullName )
   if( visualizerInfo == nil ) then 
      return
   end
   
   -- Sauvegarde dans le modèle de données lua
   visualizerInfo.scale = scale

   -- Récupération du ref du frame du visualizer
   local frameObject = getObjectFromFullName( visualizerFullName .. "_ref" )
   if( frameObject == nil ) then 
      return
   end

   -- Scale
   frameObject:setvisualizerscale( visualizerFullName, scale )

end

--------------------------------------------------------------------------------
-- setGridProperty
--------------------------------------------------------------------------------

function setGridProperty( visualizerFullName, propertyName, propertyValue )

   -- Récupération des infos de vtsConfig.celx
   local visualizerInfo = findVisualizer( visualizerFullName )
   if( visualizerInfo == nil ) then 
      return
   end
   
   -- Sauvegarde dans le modèle de données lua
   if( propertyName == "GridXyPlaneVisible" ) then 
      visualizerInfo.GridXyPlaneVisible = propertyValue
   elseif( propertyName == "GridYzPlaneVisible" ) then 
      visualizerInfo.GridYzPlaneVisible = propertyValue
   elseif( propertyName == "GridXzPlaneVisible" ) then 
      visualizerInfo.GridXzPlaneVisible = propertyValue
   elseif( propertyName == "GridXyPlaneColor" ) then 
      visualizerInfo.GridXyPlaneColor = propertyValue
   elseif( propertyName == "GridYzPlaneColor" ) then 
      visualizerInfo.GridYzPlaneColor = propertyValue
   elseif( propertyName == "GridXzPlaneColor" ) then 
      visualizerInfo.GridXzPlaneColor = propertyValue
   elseif( propertyName == "GridOpacity" ) then 
      visualizerInfo.GridOpacity = propertyValue
   elseif( propertyName == "GridLabelVisible" ) then 
      visualizerInfo.GridLabelVisible = propertyValue
   end 
   
   -- Récupération du ref du frame du visualizer
   local frameObject = getObjectFromFullName( visualizerFullName .. "_ref" )
   if( frameObject == nil ) then 
      return
   end

   -- Propriété
   if( propertyName == "GridXyPlaneVisible" or propertyName == "GridYzPlaneVisible" or propertyName == "GridXzPlaneVisible" ) then 
      frameObject:setgridreferencemarkproperty{tag=visualizerFullName, property=propertyName, visible=propertyValue}
   end

   if( propertyName == "GridXyPlaneColor" or propertyName == "GridYzPlaneColor" or propertyName == "GridXzPlaneColor" ) then 
      frameObject:setgridreferencemarkproperty{tag=visualizerFullName, property=propertyName, color=propertyValue}
   end

   if( propertyName == "GridOpacity" ) then 
      frameObject:setgridreferencemarkproperty{tag=visualizerFullName, property=propertyName, opacity=propertyValue}
   end
   
   if( propertyName == "GridLabelVisible" ) then 
      frameObject:setgridreferencemarkproperty{tag=visualizerFullName, property=propertyName, visible=propertyValue}
   end

end



--------------------------------------------------------------------------------
-- setSphericalShellProperty
--------------------------------------------------------------------------------

function setSphericalShellProperty( visualizerFullName, propertyName, propertyValue )

   -- Récupération des infos de vtsConfig.celx
   local visualizerInfo = findVisualizer( visualizerFullName )
   if( visualizerInfo == nil ) then 
      return
   end
   
   -- Sauvegarde dans le modèle de données lua
   if( propertyName == "color" ) then 
      visualizerInfo.color = propertyValue
   elseif( propertyName == "opacity" ) then 
      visualizerInfo.opacity = propertyValue
   elseif( propertyName == "labelvisible" ) then 
      visualizerInfo.labelvisible = propertyValue
   end 
   
   -- Récupération du ref du frame du visualizer
   local frameObject = getObjectFromFullName( visualizerFullName .. "_ref" )
   if( frameObject == nil ) then 
      return
   end

   -- Propriété
   if( propertyName == "color") then 
      frameObject:setvisualizerreferencemarkproperty{tag=visualizerFullName, property=propertyName, color=propertyValue}
   end

   if( propertyName == "opacity" ) then 
      frameObject:setvisualizerreferencemarkproperty{tag=visualizerFullName, property=propertyName, opacity=propertyValue}
   end
   
   if( propertyName == "labelvisible" ) then 
      frameObject:setvisualizerreferencemarkproperty{tag=visualizerFullName, property=propertyName, visible=propertyValue}
   end

end

--------------------------------------------------------------------------------
-- setAimVolumeVisible
--
-- sensorFullName : chemin du senseur au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setAimVolumeVisible( sensorFullName, isVisible )

   -- Récupération du ref de l'objet
   local sensObject = getObjectFromFullName( sensorFullName, false )

   -- Visibilité
   sensObject:setpartvisible("Frustum", isVisible)
end


--------------------------------------------------------------------------------
-- setAimContourVisible
--
-- sensorFullName : chemin du senseur au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setAimContourVisible( sensorFullName, isVisible )

   -- Récupération du ref de l'objet
   local sensObject = getObjectFromFullName( sensorFullName, false )

   -- Visibilité
   sensObject:setpartvisible("FrustumBase", isVisible)
end


--------------------------------------------------------------------------------
-- setAimTraceVisible
--
-- sensorFullName : chemin du senseur au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setAimTraceVisible( sensorFullName, isVisible )

   -- Récupération du ref de l'objet
   local sensObject = getObjectFromFullName( sensorFullName, false )

   -- Visibilité
   sensObject:setpartvisible("FrustumTrace", isVisible)
end


--------------------------------------------------------------------------------
-- setAimAxisVisible
--
-- sensorFullName : chemin du senseur au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setAimAxisVisible( sensorFullName, isVisible )

   -- Récupération du nom du senseur
   local sensorName = getObjectNameFromFullName( sensorFullName )

   -- Récupération du ref de l'objet
   local refObject = getObjectFromFullName( sensorFullName, true )

   -- Recherche de <sensorName>_sens_ref/<sensorName>_AimAxis
   local visiObject = getNamedChild( refObject, sensorName .. "_AimAxis" )

   -- Si l'objet n'est pas trouvé on sort
   if ( visiObject == nil  ) then
      return
   end

   -- Visibilité
   visiObject:setvisible( isVisible )
end


--------------------------------------------------------------------------------
-- setRoiVisible
--
-- bodyName : chemin du central body
-- roiName : nom de la ROI
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setRoiVisible( bodyName, roiName, isVisible )
   local parentObject = celestia:find( bodyName )
   local roiName = getObjectNameFromFullName( roiName )
   local found = false
   for i, roiList in pairs(gROI) do
      if( roiName == roiList[1] ) then
         found = true
         for j, tagList in pairs(roiList) do
            parentObject:setregionofinterestvisible( roiList[j], isVisible )
         end
      end
   end
   if found == false then
      celestia:log( "Could not find ROI " .. roiName )
   end
end


--------------------------------------------------------------------------------
-- setRoiTextVisible
--
-- bodyName : chemin du central body
-- roiName : nom de la ROI
-- isVisible : flag de visibilité du labe
--------------------------------------------------------------------------------

function setRoiTextVisible( bodyName, roiName, isVisible )
   local parentObject = celestia:find( bodyName )
   local roiName = getObjectNameFromFullName( roiName )
   local found = false
   for i, roiList in pairs(gROI) do
      if( roiName == roiList[1] ) then
         found = true
         for j, tagList in pairs(roiList) do
            parentObject:setregionofinteresttextvisible( roiList[j], isVisible )
         end
      end
   end
   if found == false then
      celestia:log( "Could not find ROI " .. roiName )
   end
end


--------------------------------------------------------------------------------
-- setRoiColor
--
-- bodyName : chemin du central body
-- roiName : nom de la ROI
-- color : la couleur de la ROI
--------------------------------------------------------------------------------

function setRoiColor( bodyName, roiName, color )
   local parentObject = celestia:find( bodyName )
   local roiName = getObjectNameFromFullName( roiName )
   local found = false
   for i, roiList in pairs(gROI) do
      if( roiName == roiList[1] ) then
         found = true
         for j, tagList in pairs(roiList) do
            parentObject:setregionofinterestcolor( roiList[j], color )
         end
      end
   end
   if found == false then
      celestia:log( "Could not find ROI " .. roiName )
   end
end


--------------------------------------------------------------------------------
-- setRoiContourWidth
--
-- bodyName : chemin du central body
-- roiName : nom de la ROI
-- width : epaisseur du contour
--------------------------------------------------------------------------------

function setRoiContourWidth( bodyName, roiName, width )
   local parentObject = celestia:find( bodyName )
   local roiName = getObjectNameFromFullName( roiName )
   local found = false
   for i, roiList in pairs(gROI) do
      if( roiName == roiList[1] ) then
         found = true
         for j, tagList in pairs(roiList) do
            parentObject:setregionofinterestcontourwidth( roiList[j], width )
         end
      end
   end
   if found == false then
      celestia:log( "Could not find ROI " .. roiName )
   end
end


--------------------------------------------------------------------------------
-- setRoiOpacity
--
-- bodyName : chemin du central body
-- roiName : nom de la ROI
-- opacity : l'opacité de la ROI
--------------------------------------------------------------------------------

function setRoiOpacity( bodyName, roiName, opacity )
   local parentObject = celestia:find( bodyName )
   local roiName = getObjectNameFromFullName( roiName )
   local found = false
   for i, roiList in pairs(gROI) do
      if( roiName == roiList[1] ) then
         found = true
         for j, tagList in pairs(roiList) do
            parentObject:setregionofinterestopacity( roiList[j], opacity / 100 )
         end
      end
   end
   if found == false then
      celestia:log( "Could not find ROI " .. roiName )
   end
end


--------------------------------------------------------------------------------
-- setPoiVisible
--
-- bodyName : chemin du central body
-- poiName : nom du POI
-- isVisible : visibilité du POI
--------------------------------------------------------------------------------

function setPoiVisible( bodyName, poiName, isVisible )
   local parentObject = celestia:find( bodyName )
   parentObject:setpointofinterestvisible( poiName, isVisible )
end


--------------------------------------------------------------------------------
-- setPoiTextVisible
--
--  bodyName : chemin du central body
--  poiName : nom du POI
--  isVisible : visibilit du label du POI
--------------------------------------------------------------------------------

function setPoiTextVisible( bodyName, poiName, isVisible )
   local parentObject = celestia:find( bodyName )
   parentObject:setpointofinteresttextvisible( poiName, isVisible )
end


--------------------------------------------------------------------------------
-- setPoiColor
--
-- bodyName : chemin du central body
-- poiName : nom du POI
-- color : la couleur du POI
--------------------------------------------------------------------------------

function setPoiColor( bodyName, poiName, color )
   local parentObject = celestia:find( bodyName )
   parentObject:setpointofinterestcolor( poiName, color )
end


--------------------------------------------------------------------------------
-- setAllRoiVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setAllRoiVisible( bodyFullName, isVisible )

   local parentObject = getObjectFromFullName( bodyFullName, true )

   for i, roiList in pairs(gROI) do
      for j, tagList in pairs(roiList) do
         parentObject:setregionofinterestvisible( roiList[j], isVisible )
      end
   end
end


--------------------------------------------------------------------------------
-- setAllPoiVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setAllPoiVisible( bodyFullName, isVisible )

   -- bodyFullName pour le moment pas utilisable

   t = {}
   t.landingsite = isVisible
   celestia:getobserver():setlocationflags(t)
end


--------------------------------------------------------------------------------
-- setTerminatorVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setTerminatorVisible( bodyFullName, isVisible )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )
   local sunObject = celestia:find( "Sol" )

   -- Visibilité
   if( isVisible == true ) then
      visiObject:addreferencemark{ type = "terminator" }
      visiObject:addreferencemark{type = "visible region", size = 1000, color = "yellow",
                      opacity = 1.0, tag = "SunTerminator", target = sunObject}
   else
      visiObject:removereferencemark("SunTerminator")
   end
end

--------------------------------------------------------------------------------
-- updateUmbraReferenceMark
--
-- vtsBody : body VTS
--------------------------------------------------------------------------------

function updateUmbraReferenceMark(vtsBody)

   if vtsBody.umbraVisible == false and vtsBody.penumbraVisible == false then
      vtsBody.object:removereferencemark("UmbraCone")
   else
      vtsBody.object:addreferencemark{type    = "umbra cone",
                                      size    = vtsBody.umbraConeExtent or 1e9,
                                      color   = vtsBody.umbraConeColor or "#FF28628F",
                                      tag     = "UmbraCone",
                                      visible = vtsBody.umbraVisible or false}

      vtsBody.object:addreferencemark{type    = "penumbra cone",
                                      size    = vtsBody.penumbraConeExtent or 1e9,
                                      color   = vtsBody.penumbraConeColor or "#FF28628F",
                                      tag     = "UmbraCone",
                                      visible = vtsBody.penumbraVisible or false}

   end
end


--------------------------------------------------------------------------------
-- setUmbraVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setUmbraVisible( bodyFullName, isVisible )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )
   local sunObject = celestia:find( "Sol" )

   local vtsBody = getVTSBody( visiObject:name() )
   if vtsBody ~= nil then
      vtsBody.umbraVisible = isVisible
      updateUmbraReferenceMark(vtsBody)
   end
end


--------------------------------------------------------------------------------
-- setUmbraColor
--
-- bodyFullName : chemin du body au format conventionnel
-- color : couleur du cone d'ombre
--------------------------------------------------------------------------------

function setUmbraColor( bodyFullName, color )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )

   -- On stocker la nouvelle valeur dans lua
   local vtsBody = getVTSBody( visiObject:name() )

   if vtsBody ~= nil then
      vtsBody.umbraConeColor = color
      updateUmbraReferenceMark(vtsBody)
   end

end


--------------------------------------------------------------------------------
-- setUmbraExtent
--
-- bodyFullName : chemin du body au format conventionnel
-- extent : étendu maximale du cone d'ombre de puis le centre du corps
--------------------------------------------------------------------------------

function setUmbraExtent( bodyFullName, extent )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )

   -- On stocker la nouvelle valeur dans lua
   local vtsBody = getVTSBody( visiObject:name() )

   if vtsBody ~= nil then
      vtsBody.umbraConeExtent = extent
      updateUmbraReferenceMark(vtsBody)
   end

end


--------------------------------------------------------------------------------
-- setPenumbraVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setPenumbraVisible( bodyFullName, isVisible )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )
   local sunObject = celestia:find( "Sol" )

   local vtsBody = getVTSBody( visiObject:name() )

   if vtsBody ~= nil then
      vtsBody.penumbraVisible = isVisible
      updateUmbraReferenceMark(vtsBody)
   end
end


--------------------------------------------------------------------------------
-- setPenumbraColor
--
-- bodyFullName : chemin du body au format conventionnel
-- color : couleur du cone d'ombre
--------------------------------------------------------------------------------

function setPenumbraColor( bodyFullName, color )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )

   -- On stocker la nouvelle valeur dans lua
   local vtsBody = getVTSBody( visiObject:name() )

   if vtsBody ~= nil then
      vtsBody.penumbraConeColor = color
      updateUmbraReferenceMark(vtsBody)
   end
 
end


--------------------------------------------------------------------------------
-- setPenumbraExtent
--
-- bodyFullName : chemin du body au format conventionnel
-- extent : étendu maximale du cone d'ombre de puis le centre du corps
--------------------------------------------------------------------------------

function setPenumbraExtent( bodyFullName, extent )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, true )

   -- On stocker la nouvelle valeur dans lua
   local vtsBody = getVTSBody( visiObject:name() )

   if vtsBody ~= nil then
      vtsBody.penumbraConeExtent = extent
      updateUmbraReferenceMark(vtsBody)
   end
  
end


--------------------------------------------------------------------------------
-- setVisibilityLinkVisible
--
-- Setter de visibilité des liens de visibilité station-satellite par satellite
-- 
-- satelliteFullName : chemin du satellite complet ou '*' pour tous les satellites
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setVisibilityLinkVisible( satelliteFullName, isVisible )

   -- Parcours de tous les links
   for i, visibilityLink in ipairs(visibilityLinks) do
   
      -- Parcours des liens de visibilité
      -- (ne pas utiliser satelliteFullName dans la suite car il peut valoir '*')
      if( satelliteFullName == visibilityLink[1] or satelliteFullName == "*" ) then
         -- Récupération des ref des objets si possible
         local satellite = getObjectFromFullName( visibilityLink[1], true )
         local station = getObjectFromFullName( visibilityLink[2], true )
         local body = getObjectFromFullName( visibilityLink[3], true )

         -- Ajout ou suppression du referencemark
         local linkName = "visibilitylink_" .. i
         if( isVisible ) then 
            satellite:addreferencemark{type = "visibility link", color = "yellow", tag = linkName, target = station, obstacle = body }
         else
            satellite:removereferencemark( linkName )
         end
       end
   end
end


--------------------------------------------------------------------------------
-- setClusterVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- visible : flag de visibilité
--------------------------------------------------------------------------------

function setClusterVisible( bodyFullName, visibiltyStr )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, false )
   if visiObject ~= nil then
      -- Générateur pour parcourir une éléments d'un liste de noms
      -- séparé par ','
      local chilrenNames = function( strList )
         for bodyName in string.gmatch( strList, "[^,]+" ) do
            local trimmed =  bodyName:gsub( "^%s+", "" ):gsub( "%s+$", "" )
            coroutine.yield( trimmed )
          end
      end

      -- La commande de visibilité est tout le monde visible sauf ...
      if string.find( visibiltyStr, "^all except" ) then
         -- Récupération de la liste des objets cachés
         local hiddenStrList = string.match( visibiltyStr, "all except (.*)" )
         if hiddenStrList ~= nil then
            -- Tout le monde est remis à visible
            visiObject:resetclustervisibility( true )
            visiObject:setvisible( true )
            for name in coroutine.wrap( function() return chilrenNames( hiddenStrList ) end ) do
               local childName = bodyFullName .. "/" .. name
               local childObject = getObjectFromFullName( childName, false )
               if childObject ~= nil then
                  -- Disparition des éléments choisis
                  childObject:setvisible( false )
               end
            end
         end
      -- La commande de visibilité est tout le monde caché sauf ...
      elseif string.find( visibiltyStr, "^none except" ) then
         local visibleStrList = string.match( visibiltyStr, "none except (.*)" )
         if visibleStrList ~= nil then
            -- Tout le monde est remis à caché
            visiObject:resetclustervisibility( false )
            visiObject:setvisible( true )
            for name in coroutine.wrap( function() return chilrenNames( visibleStrList ) end ) do
               local childName = bodyFullName .. "/" .. name
               local childObject = getObjectFromFullName( childName, false )
               if childObject ~= nil then
                  -- Apparition des éléments choisis
                  childObject:setvisible( true )
               end
            end
         end
      -- La commande de visibilité est tout le monde visible
      elseif string.match( visibiltyStr, "^all$" ) then
         visiObject:resetclustervisibility( true )
         visiObject:setvisible( true )
      -- La commande de visibilité est tout le monde caché
      elseif string.match( visibiltyStr, "^none$" ) then
         visiObject:setvisible( false )
      end
   end
end


--------------------------------------------------------------------------------
-- setClusterVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- visible : flag de visibilité
--------------------------------------------------------------------------------

function setClusterSymbol( bodyFullName, symbol )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, false )

   if visiObject ~= nil then
      visiObject:setclustersymbol(symbol)
   end
end


--------------------------------------------------------------------------------
-- setClusterVisible
--
-- bodyFullName : chemin du body au format conventionnel
-- visible : flag de visibilité
--------------------------------------------------------------------------------

function setClusterSymbolSize( bodyFullName, size )

   -- Récupération du ref de l'objet
   local visiObject = getObjectFromFullName( bodyFullName, false )

   if visiObject ~= nil then
      visiObject:setclustersymbolsize(size)
   end
end


--------------------------------------------------------------------------------
-- setLinkVisualizerVisible
--
-- Setter de visibilité des visualizers par satellite
-- 
-- visualizerName : nom du visualizer 
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setLinkVisualizerVisible( visualizerName, isVisible )

   -- Parcours de tous les visualizers 
   for visualizerIndex, visualizer in ipairs(visualizers) do

      if( visualizerName == visualizer.tag ) then
      
         -- Link
         if( visualizer.type == "Link" ) then 

            -- Partie spécifique du Link dans visualizer[1]
            local link = visualizer[1]

            -- Boucle sur les liens inter-satellites
            for linkIndex = 1, link.count do
               local first = getObjectFromFullName( link[linkIndex].first, true )
               local second = getObjectFromFullName( link[linkIndex].second, true )
               local body = getObjectFromFullName( link[linkIndex].obstacle, true )

               -- Tag avec un nom unique non dépendant du nom de l'entité pour gérer le "*"
               local visualizerTag = "link_" .. visualizerIndex .. "_" .. linkIndex
               if( isVisible ) then
                  first:addreferencemark{type = "visibility link", color = link.color, tag = visualizerTag, target = second, obstacle = body}
               else
                  first:removereferencemark( visualizerTag )
               end
            end
         end
      end
   end
end




--------------------------------------------------------------------------------
-- setLayerVisible
--
-- Setter de visibilité des layers d'un body
-- 
-- layerName : nom du layer (ex: "Sol/Earth/Clouds")
-- isVisible : flag de visibilité
--------------------------------------------------------------------------------

function setLayerVisible( layerName, isVisible )

   local luaLayerName = layerName:gsub("[ -/]", "_")

   -- Recherche du layer dans la table. Si non trouvé on sort
   local cmdLayer = layerTable[luaLayerName]
   if( cmdLayer == nil ) then
      return
   end

   -- Flag de visibilité mis à jour dans la table pour le layer de la commande
   cmdLayer.isVisible = isVisible 

   -- Celestia ne peut afficher qu'une seule texture alternative donc on parcourt
   -- tous les layers pour choisir le plus haut visible à affecter au layer courant
   -- currentLayer.getAltTexture est appelé continuellement dans la boucle de rendu
   -- Les layers avec une position basse sont plus prioritaires
   local maxLayerPosition = 999999
   
   -- On positionne le currentLayer à nil si aucun layer n'est visible on affectera
   -- le layer par défaut
   currentLayer = nil
   for layerIndex, projectLayer in pairs(layerTable) do
      
      -- On garde le layer visible avec la position la plus basse
      if( projectLayer.isVisible == true and projectLayer.position < maxLayerPosition ) then
         currentLayer = projectLayer
         maxLayerPosition = projectLayer.position
      end
   end
end


--------------------------------- End Of File ----------------------------------
