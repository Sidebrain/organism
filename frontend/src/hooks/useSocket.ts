import type { Message } from "@/context/AppContext";
import { BACKEND_URL } from "../../constants";
import { useEffect, useRef, useCallback } from "react";
import io from "socket.io-client";
import type { StreamingResponse } from "@/lib/EventSourceHandler";

interface SocketProps {
  setMessages: (
    messages: Message[] | ((prev: Message[]) => Message[])
  ) => void;
}

export const useSocket = ({ setMessages }: SocketProps) => {
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

      socketRef.current.on("connect", () => {
        socketRef.current?.emit("hello", "world");
      });
      socketRef.current.on("chat_stream", (delta: { data: string }) => {
        try {
          // Parse the data string from the Socket.IO event
          const parsedData: StreamingResponse = JSON.parse(delta.data);

          setMessages((prev) => {
            const existingMessageIndex = prev.findIndex(
              (msg) => msg.id === parsedData.id
            );

            if (existingMessageIndex !== -1) {
              // Update existing message
              return prev.map((msg, index) =>
                index === existingMessageIndex
                  ? {
                      ...msg,
                      content:
                        msg.content +
                        parsedData.choices[0].delta.content,
                    }
                  : msg
              );
            } else {
              // Create new message
              const newMessage: Message = {
                id: parsedData.id,
                type: "generative",
                content: parsedData.choices[0].delta.content || "",
                timestamp: new Date(),
              };
              return [...prev, newMessage];
            }
          });
        } catch (error) {
          console.error("Error parsing chat stream data:", error);
        }
      });

      socketRef.current.on("disconnect", () => {
        console.log("Disconnected from socket");
      });
    } catch (error) {
      console.error("Error connecting to socket", error);
    } finally {
      isConnectingRef.current = false;
    }
  }, [setMessages]);

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
