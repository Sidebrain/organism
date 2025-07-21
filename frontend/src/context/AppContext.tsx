import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

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

  const handleSendMessage = () => {
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      type: "human",
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputText("");
  };

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
