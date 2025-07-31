import { BACKEND_URL } from "../../constants";
import { useEffect, useRef, useCallback } from "react";
import io from "socket.io-client";

export const useSocket = () => {
  const socketRef = useRef<SocketIOClient.Socket | null>(null);
  const isConnectingRef = useRef(false);

  const connect = useCallback(() => {
    if (socketRef.current?.connected || isConnectingRef.current) {
      return;
    }
    try {
      isConnectingRef.current = true;
      const socket = io(BACKEND_URL, {
        transports: ["websocket", "polling"],
        autoConnect: true,
        timeout: 20000,
        reconnection: true,
      });
      socketRef.current = socket;

      console.log("Connected to socket");
      socketRef.current.on("connect", () => {
        console.log("Connected to socket");
        console.log("now trying to send hello");
        socketRef.current?.emit("hello", "world");
      });
      socketRef.current.on("disconnect", () => {
        console.log("Disconnected from socket");
      });
    } catch (error) {
      console.error("Error connecting to socket", error);
    } finally {
      isConnectingRef.current = false;
    }
  }, []);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      isConnectingRef.current = false;
      console.log("Disconnected from socket");
    }
  }, []);

  //clean up on umount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    socket: socketRef.current,
  };
};
