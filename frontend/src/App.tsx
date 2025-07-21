import { useEffect } from "react";
import { HumanArea } from "./components/HumanArea";
import { GenerativeArea } from "./components/GenerativeArea";
import {
  AppProvider,
  useAppContext,
  type Message,
} from "./context/AppContext";

function AppContainer() {
  const appContext = useAppContext();

  // Dummy EventSource setup
  useEffect(() => {
    const es = new EventSource("/api/events");

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const newMessage: Message = {
          id: Date.now().toString(),
          type: data.type || "generative",
          content: data.content || data.message,
          timestamp: new Date(),
        };
        appContext.setMessages((prev) => [...prev, newMessage]);
      } catch {
        console.log("EventSource data:", event.data);
      }
    };

    es.onerror = () => {
      console.log("EventSource connection failed (expected in dev)");
    };

    return () => es.close();
  }, [appContext]);

  // Dummy data for demonstration
  useEffect(() => {
    const dummyMessages: Message[] = [
      {
        id: "1",
        type: "human",
        content: "Hello, I need help with building a React component.",
        timestamp: new Date(Date.now() - 5000),
      },
      {
        id: "2",
        type: "generative",
        content: `// React Component Example\n\nimport React from 'react';\n\nfunction MyComponent() {\n  return (\n    <div className="p-4">\n      <h1>Hello World</h1>\n    </div>\n  );\n}\n\nexport default MyComponent;`,
        timestamp: new Date(Date.now() - 3000),
      },
    ];
    appContext.setMessages(dummyMessages);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Mobile View */}
      <div className="md:hidden h-full">
        <div
          className={`h-full transition-transform duration-300 ${
            appContext.showGenerative
              ? "-translate-x-full"
              : "translate-x-0"
          }`}
        >
          <HumanArea />
        </div>
        <div
          className={`absolute inset-0 transition-transform duration-300 ${
            appContext.showGenerative
              ? "translate-x-0"
              : "translate-x-full"
          }`}
        >
          <GenerativeArea />
        </div>
      </div>

      {/* Desktop View */}
      <div className="hidden md:flex h-full">
        {appContext.settings.generativeOnRight ? (
          <>
            <div className="w-1/2">
              <HumanArea />
            </div>
            <div className="w-1/2">
              <GenerativeArea />
            </div>
          </>
        ) : (
          <>
            <div className="w-1/2">
              <GenerativeArea />
            </div>
            <div className="w-1/2">
              <HumanArea />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const App = () => {
  return (
    <AppProvider>
      <AppContainer />
    </AppProvider>
  );
};

export default App;
