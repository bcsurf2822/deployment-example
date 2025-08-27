"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useSocket } from "@/components/providers/SocketProvider";

export function TestSocketSettings() {
  const { socket, isConnected } = useSocket();
  const [lastBroadcast, setLastBroadcast] = useState<string>("");
  const [receivedMessages, setReceivedMessages] = useState<Array<{ message: string; timestamp: number }>>([]);
  const [confirmationReceived, setConfirmationReceived] = useState<boolean>(false);

  useEffect(() => {
    if (!socket) return;

    const handleBroadcast = (data: { message: string; timestamp: number; userId?: string }) => {
      console.log("[TestSocketSettings-handleBroadcast] Received broadcast:", data);
      setReceivedMessages(prev => [...prev, { message: data.message, timestamp: data.timestamp }]);
    };

    const handleBroadcastReceived = (data: { 
      type: string; 
      original_message: string; 
      message: string; 
      timestamp: string; 
      from_server: boolean 
    }) => {
      console.log("[TestSocketSettings-handleBroadcastReceived] Server confirmed broadcast:", data);
      setConfirmationReceived(true);
      setReceivedMessages(prev => [...prev, { 
        message: `✅ ${data.message}`, 
        timestamp: new Date(data.timestamp).getTime() 
      }]);
      
      setTimeout(() => setConfirmationReceived(false), 3000);
    };

    socket.on("broadcast", handleBroadcast);
    socket.on("broadcast-received", handleBroadcastReceived);

    return () => {
      socket.off("broadcast", handleBroadcast);
      socket.off("broadcast-received", handleBroadcastReceived);
    };
  }, [socket]);

  const handleTestSocket = () => {
    if (!socket || !isConnected) {
      console.log("[TestSocketSettings-handleTestSocket] Socket not connected");
      return;
    }

    const testMessage = `Test broadcast at ${new Date().toLocaleTimeString()}`;
    console.log("[TestSocketSettings-handleTestSocket] Sending broadcast:", testMessage);
    
    socket.emit("broadcast", {
      message: testMessage,
      userId: "test-user"
    });
    
    setLastBroadcast(testMessage);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Socket Testing</h3>
        <p className="mt-1 text-sm text-gray-600">
          Test the WebSocket connection to the server
        </p>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <Button
            onClick={handleTestSocket}
            variant="outline"
            size="default"
            disabled={!isConnected}
          >
            Test Socket
          </Button>
          
          <div className="flex items-center space-x-2">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {lastBroadcast && (
          <div className={`p-3 rounded-md transition-colors ${confirmationReceived ? 'bg-green-50 border border-green-200' : 'bg-blue-50'}`}>
            <p className={`text-sm ${confirmationReceived ? 'text-green-900' : 'text-blue-900'}`}>
              <span className="font-medium">Last broadcast sent:</span> {lastBroadcast}
              {confirmationReceived && <span className="ml-2">✅ Confirmed by server</span>}
            </p>
          </div>
        )}

        {receivedMessages.length > 0 && (
          <div className="border rounded-md p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Received Broadcasts:</h4>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {receivedMessages.slice(-5).reverse().map((msg, idx) => (
                <div key={idx} className="text-sm text-gray-600">
                  <span className="text-xs text-gray-400">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                  {' - '}
                  {msg.message}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}