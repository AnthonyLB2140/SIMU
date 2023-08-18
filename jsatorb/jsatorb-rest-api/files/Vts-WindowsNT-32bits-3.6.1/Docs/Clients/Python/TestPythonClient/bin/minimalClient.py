#!/bin/python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# minimalClient.py
#
# Example of a minimal VTS client application in Python.
#
# For more information, please refer to the "Plugin development section" 
# of the VTS User Manual
# -----------------------------------------------------------------------------

import socket
import asyncore
import argparse
import sys

# -----------------------------------------------------------------------------
# Default variables for VTS connection
# -----------------------------------------------------------------------------

# Broker host (localhost by default)
DEFAULT_HOSTNAME = 'localhost'
# Broker port (8888 by default)
DEFAULT_PORT = 8888
# VTS application ID (-1 means Broker will assign a valid ID)
DEFAULT_APPID = -1
# Application Name
DEFAULT_APPNAME = 'MinimalClient'
# Message Encoding
BROKER_ENCODING = 'latin-1'
# Socket buffer size
BUFFER_SIZE = 8192

# -----------------------------------------------------------------------------
# VTS client class
# -----------------------------------------------------------------------------
class VTSConnection(asyncore.dispatcher):
    """ Simple class implementing the connection to VTS Broker
        Inherits from asyncore.dispatcher in order to manage 
        async event (new message on socket, ...)
    """
    
    def __init__(self, appname, appid, hostname, port):
        """ Creates an instance of VTSConnection """
        # Dispatcher intialization
        asyncore.dispatcher.__init__(self)
        
        # Create socket with asyncore.dispatcher method
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to host
        self.connect( (hostname, port) )
        
        # Send VTS INIT command
        self.buffer = 'INIT "'+appname+'" CONSTRAINT 1.0 '+str(appid)+'\n'
        
        # Define callbacks
        self.callbacks = {}
    
    def writable(self):
        """ Return true if buffer contains something """
        return (len(self.buffer) > 0)
    
    def handle_connect(self):
        """ Called when connection is established """
        print( 'Connection established.' )
    
    def handle_close(self):
        """ Called when connection is closed """
        print( 'Connection closed.' )
        self.close()
    
    def handle_read(self):
        """ Called when a message is received from Broker """
        # Read data from the socket
        # NOTE: Commands may be lost if data does not fit in buffer
        command_string = self.recv(BUFFER_SIZE).decode(BROKER_ENCODING)
        
        # Commands end with a new line (\n)
        command_list = command_string.split('\n')
        
        # Execution of the user function associated with the command
        for command in command_list:
            # Search if there is a callback
            for key in self.callbacks.keys():
                if command.startswith(key):
                    self.callbacks[key](command)
    
    def handle_write(self):
        """ Called when a message is send to the Broker """
        # Write in 'sent' the size of sent string
        sent = self.send(self.buffer.encode(BROKER_ENCODING))

        # Write in buffer non-sent string
        self.buffer = self.buffer[sent:]

    def register_callback(self, command_prefix, callback):
        """ Registers a callback for the specified command prefix
            * command_prefix represents the prefix of a full command
                ex :'TIME' for command 'TIME 3.2123123 2'
                ex : 'CMD PR' for command 'CMD PROP color red'
            * callback is the user function that will be called with 
              the command string
        """
        self.callbacks[command_prefix] = callback

# -----------------------------------------------------------------------------
# User Functions
# -----------------------------------------------------------------------------

def process_time(command):
    print('Received time: %s' % command)
    sys.stdout.flush()

# -----------------------------------------------------------------------------
# Main 
# -----------------------------------------------------------------------------

def main(appname, appid, host, port):
    # Creates a VTS client and connects to Broker
    client = VTSConnection(appname, appid, host, port)
    
    # Associate a user function to the TIME command
    client.register_callback('TIME', process_time)
    
    # Wait for messages
    asyncore.loop()

if __name__ == '__main__':
    # Parse arguments for main function
    parser = argparse.ArgumentParser(description='Minimal VTS client application')
    parser.add_argument('--appid', default=DEFAULT_APPID,
                   help='VTS application ID')
    parser.add_argument('--serverhost', default=DEFAULT_HOSTNAME,
                   help='Specify custom Broker host')
    parser.add_argument('--serverport', default=DEFAULT_PORT,
                   help='Specifiy custom Broker port') 
    args = parser.parse_args()
    
    main(DEFAULT_APPNAME, args.appid, args.serverhost, args.serverport)
