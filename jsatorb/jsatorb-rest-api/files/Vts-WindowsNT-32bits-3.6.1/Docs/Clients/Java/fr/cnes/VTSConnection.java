// -----------------------------------------------------------------------------
// VTSConnection.java
//
// Example of a minimal VTS client application in Python.
//
// For more information, please refer to the "Plugin development section" 
// of the VTS User Manual
// -----------------------------------------------------------------------------
package fr.cnes;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;
import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Set;

/**
 * Callback interface for processing commands
 */
interface VTSCallback
{
    /** 
     * Called when the callback is executed 
     * @param command  the full string command 
     */
    void run(String command);
}

/**
 * VTSReader reads from buffer and executes command callbacks
 */
class VTSReader implements Runnable
{
    private BufferedReader buffer_;

    /**
     * Initialize VTSReader with a stream buffer
     * @param buffer
     */
    VTSReader( BufferedReader buffer )
    {
        this.buffer_ = buffer;
    }

    /**
     * Endless loop, read buffer
     */
    @Override
    public void run()
    {
        while(true)
        {
            try
            {
                // Read one line on buffer
                String message = this.buffer_.readLine();

                // Search if some key correspond to start of command
                Set<String> keys = handlers.keySet();
                for ( String key : keys )
                {
                    if( message.startsWith(key) )
                    {
                        // If yes, execute VTSCallback associate command
                        handlers.get(key).run(message);
                    }

                }
            }
            catch (IOException e)
            {
                e.printStackTrace();
            }
        }
    }
    
    // Callbacks
    static public HashMap<String, VTSCallback> handlers = new HashMap<String, VTSCallback>();
}

/**
 * Connection to VTS Broker
 */
public class VTSConnection
{
    /**
     * VTSConnection constructor
     * @param appName   Application name
     * @param appId     Application ID
     * @param hostname  Broker Hostname
     * @param port      Broker Port
     */
    VTSConnection(String appName, String appId, String hostname, String port) throws IOException
    {
        try
        {
            // Create socket to connect to broker
            serverSocket_ = new Socket(hostname, Integer.parseInt(port));

            // Create buffer to read on socket and detach it in new thread
            BufferedReader buffer = new BufferedReader(new InputStreamReader(serverSocket_.getInputStream()));
            tVtsReader_ = new Thread(new VTSReader( buffer ));
            tVtsReader_.start();

            // Create a writer to send data to broker
            vtsWriter_ = new PrintWriter(serverSocket_.getOutputStream());

            // Send init data to broker with appname and appid
            this.send("INIT \""+appName+"\" CONSTRAINT 1.0 "+appId);

        }
        catch  (UnknownHostException e)
        {
            e.printStackTrace();
            return;
        }
    }

    public void send(String data)
    {
        // Print some data in buffer
        vtsWriter_.println(data);
        // Send data by flushing buffer
        vtsWriter_.flush();
    }

    public void registerCallback(String command, VTSCallback callback)
    {
        // Link command to callback class
        VTSReader.handlers.put(command, callback);
    }
    
    private Thread tVtsReader_;
    private PrintWriter vtsWriter_;
    private Socket serverSocket_;
}
