import {
  createContext,
  useContext,
  useState,
  useRef,
  useCallback,
  type ReactNode,
} from "react";
import { EventSourceHandler } from "@/lib/EventSourceHandler";
import { BACKEND_URL } from "../../constants";

export interface Message {
  id: string;
  type: "human" | "generative";
  content: string;
  timestamp: Date;
}

export interface Settings {
  generativeOnRight: boolean;
}

interface AppContextType {
  messages: Message[];
  setMessages: (
    messages: Message[] | ((prev: Message[]) => Message[])
  ) => void;
  inputText: string;
  setInputText: (inputText: string) => void;
  showGenerative: boolean;
  setShowGenerative: (showGenerative: boolean) => void;
  settings: Settings;
  setSettings: (
    settings: Settings | ((prev: Settings) => Settings)
  ) => void;
  handleSendMessage: () => void;
  humanMessages: Message[];
  generativeMessages: Message[];
}

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [showGenerative, setShowGenerative] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    generativeOnRight: true,
  });

  const eventSourceRef = useRef<EventSourceHandler | null>(null);

  const startStreaming = useCallback(async () => {
    const streamingMessageId = `msg_${Date.now()}`;

    // Create placeholder generative message
    const placeholderMessage: Message = {
      id: streamingMessageId,
      type: "generative",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, placeholderMessage]);

    // Create new EventSource for this streaming session
    const eventSource = new EventSourceHandler({
      url: `${BACKEND_URL}/v1/chat/stream`,
      onDelta: (content: string) => {
        // Always use our local streamingMessageId, ignore backend messageId
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === streamingMessageId
              ? { ...msg, content: msg.content + content }
              : msg
          )
        );
      },
      onDone: (messageId?: string) => {
        console.log("Streaming completed for message:", messageId);
        if (eventSourceRef.current) {
          eventSourceRef.current.disconnect();
          eventSourceRef.current = null;
        }
      },
      onConnectionChange: (connected: boolean) => {
        console.log(
          "Connection status changed:",
          connected ? "connected" : "disconnected"
        );
      },
      onError: (error: string) => {
        console.error("EventSource connection failed:", error);
      },
    });

    eventSourceRef.current = eventSource;
    eventSource.connect();

    // The EventSource connection should be sufficient to trigger streaming

    return streamingMessageId;
  }, []);

  const handleSendMessage = useCallback(() => {
    if (!inputText.trim()) return;

    // Create human message
    const newMessage: Message = {
      id: Date.now().toString(),
      type: "human",
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputText("");

    // Trigger streaming for the response
    startStreaming();
  }, [inputText, startStreaming]);

  const humanMessages = messages.filter((m) => m.type === "human");
  const generativeMessages = messages.filter(
    (m) => m.type === "generative"
  );

  return (
    <AppContext.Provider
      value={{
        messages,
        setMessages,
        inputText,
        setInputText,
        showGenerative,
        setShowGenerative,
        settings,
        setSettings,
        handleSendMessage,
        humanMessages,
        generativeMessages,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
};
