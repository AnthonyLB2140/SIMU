--------------------------------------------------------------------------------
-- vts.lua
--
-- Copyright © (2020) CNES All rights reserved
--
-- VER : $Id: vts.lua 8957 2021-11-03 15:22:36Z mmo $
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- Utilisation des modules externes
--------------------------------------------------------------------------------

socket = require( "socket" )
require( "vtsMath" )
require( "vtsCamera" )
require( "vtsClient" )


--------------------------------------------------------------------------------
-- initSocket
--
-- Creer un socket dans un etat initial
--------------------------------------------------------------------------------

function initSocket()

   local f
   local line

   -- Initialisation de l'objet realtime
   rt = {}

   -- Lecture du serveur Celestia et du port
   rt.servername = "localhost"
   rt.port = serverPort

   -- Initialisations diverses
   rt.time = 0.0
   rt.realTime = 0.0
   rt.lastConnectAttempt = 0.0
   rt.connected = false
   rt.paused = false
   rt.sendSync = false

   rt.client = socket.tcp()
   rt.objects = {}
   rt.streamInfos = {}
   rt.lastReceivedCamera = {}
   rt.lastMessage = ""
   rt.multi = {}
   rt.multi.sep = "|"
   rt.multi.h = 1
   rt.multi.v = 1
   
   rt.sensorCamOffset = -1 / uly2m

end


--------------------------------------------------------------------------------
-- connectToServer
--
-- Tentative de connexion au serveur de donnees
--------------------------------------------------------------------------------

function connectToServer( )

   -- Si la derniere tentative de connexion a plus de 1 secondes
   if( rt.time - rt.lastConnectAttempt > 1 ) then

      -- Memorisation de la date de la tentative
      rt.lastConnectAttempt = rt.time

      -- Tentative de connexion
      rt.client:settimeout( 1 )
      local result, errmsg = rt.client:connect( rt.servername, rt.port )
       rt.client:settimeout( 0 )

      -- Test de la connexion
      if( result == 1 ) then
         rt.connected = true
      end

      -- Affichage d'un message d'information
      if rt.connected then
         celestia:log( "Connected !" )

         -- Initialisation des corps du système solaire
         initStandardBodies()

         -- Android Experiment JEE
         -- Appel à ne pas supprimer sinon les fonctions utilisant ces objets ne marcheront plus.
         -- initCameraAndroid()

         -- Exécution du script de définition des fonctions de texture variable
         hasAltTexture = false
         textureScriptPath = celestia:getvtsextradir() .. "/VTS/vtsTexture.celx"
         local textureScriptFile = io.open( textureScriptPath, "r" )
         if textureScriptFile~=nil then
            io.close( textureScriptFile )
            dofile( textureScriptPath )
         end
         currentTex = ""

         -- Exécution du script de chargement des fichiers de Régions d'Intérêt
         local roiScriptPath = celestia:getvtsextradir() .. "/VTS/vtsInitROI.celx"
         local roiScriptFile = io.open( roiScriptPath, "r" )
         if roiScriptFile~=nil then
            io.close( roiScriptFile )
            dofile( roiScriptPath )
         end

         -- Envoi de la commande d'init
         -- celestiaAppId et realClientName sont définis dans vtsConfig.celx
         local initCommand = "INIT " .. realClientName .. " CONSTRAINT 1.0 " .. celestiaAppId .. "\n"

         local nbbytes, errorsend = rt.client:send(initCommand)
         -- Si aucun message n'a ete ecrit dans la socket
         if ( nbbytes == nil  ) then
            celestia:log( "Error connecting server : " .. errorsend )
         else
            celestia:log( "Connected to " .. rt.servername .. "(" ..
                          rt.port .. "), sent bytes: " .. nbbytes )
         end
      else
         celestia:log( "Trying to connect to " .. rt.servername .. "..." )
         celestia:log( "Cannot connect to " .. rt.servername .. "(" ..
            rt.port .. "): " .. errmsg )
      end

   end

end


--------------------------------------------------------------------------------
-- lineSplit
--
-- Séparation de la ligne de données reçues en mots avec prise en compte des
-- double quotes.
--------------------------------------------------------------------------------

function lineSplit( lineToSplit )

   local totalCount = 1
   local tab = {}
   
   -- Parcours de la ligne à splitter
   -- Le split se fait par espace, mais il faut prendre en compte les ensembles quotés
   
   -- Indique si on est en échappement ou pas
   local escaping = false
   
   -- Indique si on est dans un quote
   local quoting = false
   
   -- Contient le mot en cours
   local token = ""
   
   -- Fonction d'insertion d'un token
   insertToken = function()
      if (token ~= "") then
         tab[totalCount] = token
         totalCount = totalCount + 1
	     token = ""
      end
   end
   
   -- Parcours de la chaîne
   for i = 1, string.len(lineToSplit) do
      -- Extraction du caractère courant
      local c = lineToSplit:sub(i, i)
	  	  
	  -- Espace : le token est fini
	  if (c == ' ') then
	     if (quoting == true) then
		    token = token .. c
	     else
            insertToken(token)
	     end
		 
      -- Début ou fin de quote
	  elseif (c == '\"') then
		 if (escaping == true) then
		    -- on échappait, donc on doit insérer le caractère
			token = token .. c
	     else
		    -- on n'échappait pas
			if (quoting == true) then
			   -- fin de quote, on conserve le token et on arrête le quoting
			   quoting = false
               insertToken(token)
			else
			   -- début de quote
			   quoting = true
			end
		 end
		 
	  -- Caractère d'échappement
      elseif (c == '\\') then
	     if (quoting == true) then
	        -- Dans un quote c'est un caractère d'échappement
		    if (escaping == true) then
		       -- on echappait déjà, donc on doit insérer le caractère
		  	   token = token .. c
	        else
		       -- on n'échappait pas encore
		  	   escaping = true
	        end
		 else
		    -- en dehors d'un quote c'est un caractère normal
			token = token .. c
		 end
		 
	  -- Tout autre caractère
	  else
	     -- Cas général : ni espace ni guillement
	     token = token .. c
	  end
   end
   
   -- Il peut rester un token à insérer
   insertToken(token)
   
   return tab
end


--------------------------------------------------------------------------------
-- tick
--
-- Fonction appelee par Celestia a chaque avance dans le temps (rafraichissement
-- complet de l'affichage).
--
-- dt : temps en seconde ecoule depuis le dernier appel
--------------------------------------------------------------------------------

hooks = {}
function hooks:tick( dt )

   -- Avance du temps local
   rt.ptime = rt.time
   rt.time = rt.time + dt

   -- Verification de la connexion
   if not rt.connected then

      -- Mise en pause de Celestia
      celestia:settimescale( 0 )
      
      -- Caméra par défaut pendant le chargement + message
      if( rt.firstConnectionAttempt == nil ) then
         rt.firstConnectionAttempt = true
         setCameraSynchronous( "Sol", "Sol", "+X", 0.33 )
         celestia:log( "Loading..." ) 
      end         

      -- Connexion
      connectToServer()

   else

      -- We're already connected; attempt to read from the socket. We've set
      -- the timeout to a very low value, so the read is effectively non-
      -- blocking.
      -- TODO: this is not very efficient; investigate using select() instead

      -- Depuis la réception de la demande de synchronisation, on a fait une boucle d'affichage
      if( rt.sendSync == true ) then
         rt.client:send( "CMD SERVICE Synchronized\n" )
         rt.sendSync = false
      end
      
      -- Remise à zéro des dimensions mémorisées
      rt.width = 0

      -- Lecture du premier message
      local msg, err, partial = rt.client:receive('*l')

      -- Si un message a ete lu dans la socket
      while msg ~= nil and #msg > 0 do

         -- Split the record received from the socket into separate words
         rt.values = lineSplit( msg )
         rt.lastMessage = msg

         -- Test du type de paquet recu
         if ( rt.values[1] == "DATA" ) then

            -- Memorisation de l'heure de la reception
            rt.pRealTime = rt.realTime
            rt.realTime = rt.time

            -- Traitement de la reception d'un paquet de donnees
            receiveData()

         -- Teste la reception d'une commande
         elseif ( rt.values[1] == "TIME" ) then

            -- Traitement de la reception d'un paquet temps
            receiveTime()

         -- Teste la reception d'une commande
         elseif ( rt.values[1] == "CMD" ) then

            -- Traitement de la reception d'un paquet de commande
            local continueLoop = receiveCmd()
            if( continueLoop == false ) then
               break
            end

         -- Teste la reception d'un paquet inconnu
         else
            celestia:log( "Unknown protocol command received" )
         end

        -- Lecture du message suivant
        msg, err, partial = rt.client:receive('*l')

      end

   end

   -- Android Experiment JEE
   -- if( boolHookCodeAndroid == true ) then
   --    hookTestCodeAndroid( dt )
   -- end

   return false

end


--------------------------------------------------------------------------------
-- sendimage
--
-- Fonction appelée spécifiquement pour VTS quand Cosmographia fait un rendu 
-- sans overlay de la scène et pousse l'image vers lua de manière asynchrone
-- après un appel à celestia:capturebuffertostring( "image" )
--
-- str : la chaîne représentant l'image en base64 à envoyer
--------------------------------------------------------------------------------

function hooks:sendimage( str )

   -- Construction de la commande
   local cmdToSend = "DATA 0 image " .. str .. "\n"

   -- Timeout de 10 secondes pour le transfert
   rt.client:settimeout( 10, 'b' )
   local b,err = rt.client:send( cmdToSend )
   rt.client:settimeout( 0, 'b' )
end


--------------------------------------------------------------------------------
-- Enregistrement de l'objet contenant les fonctions crochets
--------------------------------------------------------------------------------

celestia:setluahook( hooks )


--------------------------------------------------------------------------------
-- Pas de buffering pour les output (mieux pour le debug)
--------------------------------------------------------------------------------

io.stdout:setvbuf( "no" )


--------------------------------------------------------------------------------
-- On force la locale Ã  C pour utiliser le point comme sÃ©parateur dÃ©cimal
--------------------------------------------------------------------------------

os.setlocale( 'C', 'numeric' )


--------------------------------------------------------------------------------
-- Initialisations
--------------------------------------------------------------------------------

-- Exécution du script de config généré par le launcher Celestia pour positionner certaines variables dynamiques
dofile(celestia:getvtsextradir() .. "/VTS/vtsConfig.celx")

initSocket()
initSimulation()



--------------------------------- End Of File ----------------------------------
