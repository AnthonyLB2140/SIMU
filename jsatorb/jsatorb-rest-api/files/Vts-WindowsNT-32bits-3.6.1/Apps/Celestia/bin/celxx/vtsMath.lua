--------------------------------------------------------------------------------
-- vtsMath.lua
--
-- Copyright © (2019) CNES All rights reserved
--
-- VER : $Id: vtsMath.lua 8957 2021-11-03 15:22:36Z mmo $
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Definitions globales
--------------------------------------------------------------------------------

uly2m = 9460730472.5808
ulyToKm = 9460730.4725808


--------------------------------------------------------------------------------
-- multQuat
--
-- Retourne le produit de quaternions celRot1 x celRot2  (rotation Celestia)
--------------------------------------------------------------------------------

function multQuat( celRot1, celRot2 )

   local q1w = celRot1.w
   local q1x = celRot1.x
   local q1y = celRot1.y
   local q1z = celRot1.z

   local q2w = celRot2.w
   local q2x = celRot2.x
   local q2y = celRot2.y
   local q2z = celRot2.z

   local resw = -q1x * q2x - q1y * q2y - q1z * q2z + q1w* q2w
   local resx = q1x * q2w + q1y * q2z - q1z * q2y + q1w * q2x
   local resy = -q1x * q2z + q1y * q2w + q1z * q2x + q1w * q2y
   local resz = q1x * q2y - q1y * q2x + q1z * q2w+ q1w * q2z

   return celestia:newrotation( resw, resx, resy, resz )

end


--------------------------------------------------------------------------------
-- getQuatNorm
--
-- Retourne la norme d'un quaternion
--------------------------------------------------------------------------------

function getQuatNorm( celRot )
   return celRot.w * celRot.w + celRot.x * celRot.x + celRot.y * celRot.y + celRot.z * celRot.z
end


--------------------------------------------------------------------------------
-- invQuat
--
-- Retourne le quaternion inversé
--------------------------------------------------------------------------------

function invQuat( celRot )

   local normRot = getQuatNorm( celRot )

   if (normRot > 0.0) then
      local invNorm = 1.0 / normRot
      local resw = celRot.w * invNorm
      local resx = celRot.x * -invNorm
      local resy = celRot.y * -invNorm
      local resz = celRot.z * -invNorm
      return celestia:newrotation( resw, resx, resy, resz )
   end

   return nil

end

--------------------------------------------------------------------------------
-- crossProduct
-- Définition de la fonction produit vectoriel
--------------------------------------------------------------------------------
function crossProduct(u, v)

    uv = celestia:newvector( u:gety()*v:getz()-u:getz()*v:gety(),
                             u:getz()*v:getx()-u:getx()*v:getz(),
                             u:getx()*v:gety()-u:gety()*v:getx()
                           )
    return uv

end


--------------------------------------------------------------------------------
-- jjCnes2jjCel
--
-- Passage du temps JD1950 en temps JD Celestia
-- Calcul du nombre de secondes intercalaires a ajouter
--------------------------------------------------------------------------------

function jjCnes2jjCel( jjCnes )

   local leap = 10
   if( jjCnes > 8217  ) then leap = leap + 1 end
   if( jjCnes > 8401  ) then leap = leap + 1 end
   if( jjCnes > 8766  ) then leap = leap + 1 end
   if( jjCnes > 9131  ) then leap = leap + 1 end
   if( jjCnes > 9496  ) then leap = leap + 1 end
   if( jjCnes > 9862  ) then leap = leap + 1 end
   if( jjCnes > 10227 ) then leap = leap + 1 end
   if( jjCnes > 10592 ) then leap = leap + 1 end
   if( jjCnes > 10957 ) then leap = leap + 1 end
   if( jjCnes > 11504 ) then leap = leap + 1 end
   if( jjCnes > 11869 ) then leap = leap + 1 end
   if( jjCnes > 12234 ) then leap = leap + 1 end
   if( jjCnes > 12965 ) then leap = leap + 1 end
   if( jjCnes > 13879 ) then leap = leap + 1 end
   if( jjCnes > 14610 ) then leap = leap + 1 end
   if( jjCnes > 14975 ) then leap = leap + 1 end
   if( jjCnes > 15522 ) then leap = leap + 1 end
   if( jjCnes > 15887 ) then leap = leap + 1 end
   if( jjCnes > 16252 ) then leap = leap + 1 end
   if( jjCnes > 16801 ) then leap = leap + 1 end
   if( jjCnes > 17348 ) then leap = leap + 1 end
   if( jjCnes > 17897 ) then leap = leap + 1 end
   if( jjCnes > 20454 ) then leap = leap + 1 end
   if( jjCnes > 21550 ) then leap = leap + 1 end
   if( jjCnes > 22827 ) then leap = leap + 1 end
   if( jjCnes > 23922 ) then leap = leap + 1 end
   if( jjCnes > 24472 ) then leap = leap + 1 end
   
   local tai2tt   = 32.184
   local refDelta = 2433282.5

   return jjCnes + refDelta + ( leap + tai2tt ) / 86400 
          + 0.001 / 86400 -- Imprécision entre VTS et Celestia

end


--------------------------------------------------------------------------------
-- rInertiel2rCelestia
--
-- Passage du quaternion en coordonnees Celestia
--------------------------------------------------------------------------------

function rInertiel2rCelestia( q )

   local racine = math.sqrt( 2 ) / 2 ;
   local qCel = {} ;

   -- Rotation de 90 selon x
   qCel.w = - q.w * racine - q.x * racine
   qCel.x = - q.w * racine + q.x * racine
   qCel.y =   q.z * racine + q.y * racine
   qCel.z =   q.z * racine - q.y * racine

   return qCel

end

--------------------------------- End Of File ----------------------------------
