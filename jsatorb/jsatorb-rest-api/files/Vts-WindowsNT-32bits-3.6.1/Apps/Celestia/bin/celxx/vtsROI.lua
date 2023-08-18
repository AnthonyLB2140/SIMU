--------------------------------------------------------------------------------
-- vtsROI.lua
--
-- Copyright © (2020) CNES All rights reserved
--
-- VER : $Id: vtsROI.lua 8957 2021-11-03 15:22:36Z mmo $
--------------------------------------------------------------------------------



--------------------------------------------------------------------------------
-- loadRegionOfInterestFile
--
-- polygonFilePath : chemin du fichier polygone
-- targetFullPath : chemin de l'entité cible pour la ROI
-- name :nom de la ROI
-- color : couleur de la ROI
-- opacity : opacité en pourcent
--------------------------------------------------------------------------------

function 
loadRegionOfInterestFile
(
   polygonFilePath, 
   targetFullPath, 
   name, 
   color, 
   opacity,
   isclosed 
)
   -- check file exists
   local f = io.open(polygonFilePath, "r")
   if f == nil then 
      return 
   end  
   
   if isclosed == 0 then
      marktype = "LOI"
   else
      marktype = "ROI"
   end

   -- Récupération du corps central
   local target = celestia:find( targetFullPath ) 

   -- Création d'un reference mark
   local refmarktable={}
   refmarktable.type = "roi"
   refmarktable.color = color
   refmarktable.opacity = opacity / 100.
   refmarktable.tag = name
   refmarktable.polygon = polygon
   refmarktable.isclosed = isclosed
   
   -- Stockage des tags de la ROI
   gRoiCount = gRoiCount + 1
   gROI[ gRoiCount ] = {}
   gROI[ gRoiCount ][ 1 ] = name

   -- Chargement du fichier polygone en mémoire
   io.input(polygonFilePath)
   local lines = {}
   for line in io.lines() do
      table.insert(lines, line)
   end
   io.input():close()
   
   local polyTable = {}
   local polygon = ""
   local polyCount = 0
   
   -- Parcours des lignes
   for i, l in ipairs(lines) do
   
      -- Nouveau polygone
      if l == "#newpoly" then
      
         polyCount = polyCount + 1

         -- Finalisation 
         polygon = table.concat(table.reverse(polyTable)," ")
         refmarktable.polygon = polygon
         target:addreferencemark(refmarktable)

         -- Début d'un nouveau polygone (nouveau refmark)
         refmarktable.tag = name .. "_multi_" .. polyCount 
         polyTable = {}

         -- Stockage du tag de la ROI du nouveau polygone
         gROI[ gRoiCount ][ polyCount + 1 ] = refmarktable.tag

      else
         -- Lecture d'une coordonnée
         longLat = {}
         for token in string.gmatch(l, "[^%s]+") do
            table.insert(longLat, token)
         end

         table.insert(polyTable, longLat[2])
         table.insert(polyTable, longLat[1])
     
         -- Pour les LOI on dispose d'une 3eme coordonnee
         if marktype == "LOI" then
            table.insert(polyTable, longLat[3])
         end 
      end
   end

   -- Finalisation
   polygon = table.concat(table.reverse(polyTable)," ")
   refmarktable.polygon = polygon

   target:addreferencemark(refmarktable)

end


--------------------------------------------------------------------------------
-- table.reverse
--
-- Inverser une table
--------------------------------------------------------------------------------

function table.reverse ( tab )
    local size = #tab
    local newTable = {}

    for i,v in ipairs ( tab ) do
        newTable[size-i + 1] = v
    end

    return newTable
end




--------------------------------- End Of File ----------------------------------
