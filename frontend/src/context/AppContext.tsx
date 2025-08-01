import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import { useSocket } from "@/hooks/useSocket";
import type { StreamingResponse } from "@/lib/EventSourceHandler";
import {
  updateMessagesWithStreamData,
  createHumanMessage,
} from "@/lib/messageUtils";

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
  isConnected: boolean;
  emit: (event: string, data?: unknown) => void;
}

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [showGenerative, setShowGenerative] = useState(false);
  const [settings, setSettings] = useState<Settings>({
    generativeOnRight: true,
  });

  const handleChatStream = useCallback((data: StreamingResponse) => {
    setMessages((prev) => updateMessagesWithStreamData(prev, data));
  }, []);

  const { isConnected, emit } = useSocket({
    onChatStream: handleChatStream,
  });

  const handleSendMessage = useCallback(() => {
    if (!inputText.trim()) return;

    const newMessage = createHumanMessage(inputText);
    setMessages((prev) => [...prev, newMessage]);
    setInputText("");

    emit("request_chat_stream", {
      message: inputText,
    });
  }, [inputText, emit]);

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
        isConnected,
        emit,
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
