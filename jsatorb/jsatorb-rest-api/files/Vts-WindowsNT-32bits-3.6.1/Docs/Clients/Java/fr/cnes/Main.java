// -----------------------------------------------------------------------------
// Main.java
//
// Example of a minimal VTS client application in Python.
//
// For more information, please refer to the "Plugin development section" 
// of the VTS User Manual
// -----------------------------------------------------------------------------
package fr.cnes;

import java.io.IOException;
import java.util.HashMap;
import java.util.Set;

/**
 * Main class
 *
 *      Accept some comand line parameters
 *          --serverhostname Broker hostname
 *          --serverport Broker port
 *          --appid Application ID
 */
public class Main {
    // Broker host (localhost by default)
    static public String DEFAULT_HOSTNAME = "localhost";
    // Broker port (8888 by default)
    static public String DEFAULT_PORT = "8888";
    // VTS application ID (-1 means Broker will assign a valid ID)
    static public String DEFAULT_APPID = "-1";

    public static void main(String[] args) throws IOException, InterruptedException
    {
        // Parse argument from command line
        HashMap<String, String> arguments = parseArguments( args );
        String serverhostname = arguments.get( "serverhostname" );
        String serverport = arguments.get( "serverport" );
        String appid = arguments.get( "appid" );

        // Create vts client from VTSConnection class
        //  It's a simple client for VTS Broker
        VTSConnection client = new VTSConnection("MinimalClient", appid, serverhostname, serverport);

        // Link a user function to TIME commands
        client.registerCallback("TIME", new VTSCallback() {
            @Override
            public void run(String command) {
                System.out.println(command);
            }
        });
    }

    /**
     * Function to parse arguments
     */
    static public HashMap<String, String> parseArguments( String[] args )
    {
        // Get arguments from command line
        HashMap<String, String> arguments = new HashMap<String, String>();
        arguments.put( "serverhostname", DEFAULT_HOSTNAME);
        arguments.put( "serverport", DEFAULT_PORT);
        arguments.put( "appid", DEFAULT_APPID);

        Set<String> keys = arguments.keySet();
        for( int i = 0; i < args.length; ++i )
        {
            String argument = args[i];
            for ( String key : keys )
            {
                if( argument.equals("--"+key) && i + 1 < args.length)
                {
                    arguments.put(key, args[i+1]);
                    break;
                }
            }
        }
        return arguments;
    }
}
