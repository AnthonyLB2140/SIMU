#/usr/bin/env tclsh
# -----------------------------------------------------------------------------
# minimalClient.tcl
#
# Example of a minimal VTS client application in TCL.
# 
# For more information, please refer to the "Plugin development section" 
# of the VTS User Manual
# -----------------------------------------------------------------------------

# This package need tcllib installation
package provide app-VTS-TclClient 1.0
package require cmdline

# -----------------------------------------------------------------------------
# Default variables for VTS connection
# -----------------------------------------------------------------------------

# Broker host (localhost by default)
set DEFAULT_HOSTNAME "localhost"
# Broker port (8888 by default)
set DEFAULT_PORT 8888
# VTS application ID (-1 means Broker will assign a valid ID)
set DEFAULT_APPID -1
# Application Name
set DEFAULT_APPNAME "MinimalClient"

# -----------------------------------------------------------------------------
# Read a message from Broker
# -----------------------------------------------------------------------------

proc ReadSocket {sock} {
    # Detection de la fermeture de la connexion
    if [eof $sock] {
        puts "### Connection terminated."
        exit
    }
     
    # Read data from broker
    set dataFromSocket [gets $sock]
    
    # Split commands separated by line feed
    set cmds [split $dataFromSocket \n]

    # Get user functions from global namespace
    global userfunctions

    foreach cmd $cmds {
        # Seach if command is referenced
        foreach {name value} [array get userfunctions] {
            if { [string first $name $cmd] == 0 } {
                # Start referenced function
                $value $cmd
            }
        }
    }
}

# -----------------------------------------------------------------------------
# User Functions
# -----------------------------------------------------------------------------

proc process_time { cmd } {
    puts "> $cmd"
} 

proc process_cmd_time { cmd } {
    puts "> $cmd"
} 

# -----------------------------------------------------------------------------
# Main function
# -----------------------------------------------------------------------------

if {[catch {

    # Parsing arguments from command line
    set argument_hostname [list serverhostname.arg $DEFAULT_HOSTNAME "VTS Broker hostname" ]
    set argument_port     [list serverport.arg     $DEFAULT_PORT     "VTS Broker port" ]
    set argument_appid    [list appid.arg          $DEFAULT_APPID    "VTS Application ID" ]
    set parameters [list $argument_hostname $argument_port $argument_appid ]

    # Get options from cmd line
    array set options [cmdline::getoptions ::argv $parameters "VTS Connection to Broker"]

    # Get userfunctions function from global namespace
    global userfunctions

    # Associate user function to commands
    # i.e.: 'TIME' command -> 'process_time'
    #       Commands starting with 'TIME' will be processed with 'process_time'
    # NOTE: Spaces need to be escaped ("CMD TIME" -> CMD\ TIME)
    lappend userfunctions(TIME) process_time
    lappend userfunctions(CMD\ TIME) process_cmd_time

    # Open socket to connect on broker
    set sock [socket $options(serverhostname) $options(serverport) ]
    fconfigure $sock -buffering line

    # Linking socket to 'ReadSocket' function
    fileevent $sock readable [list ReadSocket $sock]

    # Client initialization
    puts $sock "INIT $DEFAULT_APPNAME CONSTRAINT 1.0 $options(appid) "

    # Wait for some commands from Vroker
    vwait forever
} msg]} {
    puts stderr "### Whoops! Something went wrong:"
    puts stderr $msg
    exit
}