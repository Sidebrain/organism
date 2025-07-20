import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

interface Message {
  id: string;
  type: "human" | "generative";
  content: string;
  timestamp: Date;
}

interface Settings {
  generativeOnRight: boolean;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [showGenerative, setShowGenerative] = useState(false);
  const [settings, setSettings] = useState<Settings>({ generativeOnRight: true });
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Dummy EventSource setup
  useEffect(() => {
    const es = new EventSource('/api/events');

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const newMessage: Message = {
          id: Date.now().toString(),
          type: data.type || "generative",
          content: data.content || data.message,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, newMessage]);
      } catch {
        console.log("EventSource data:", event.data);
      }
    };

    es.onerror = () => {
      console.log("EventSource connection failed (expected in dev)");
    };

    return () => es.close();
  }, []);

  // Dummy data for demonstration
  useEffect(() => {
    const dummyMessages: Message[] = [
      {
        id: "1",
        type: "human",
        content: "Hello, I need help with building a React component.",
        timestamp: new Date(Date.now() - 5000)
      },
      {
        id: "2", 
        type: "generative",
        content: `// React Component Example\n\nimport React from 'react';\n\nfunction MyComponent() {\n  return (\n    <div className="p-4">\n      <h1>Hello World</h1>\n    </div>\n  );\n}\n\nexport default MyComponent;`,
        timestamp: new Date(Date.now() - 3000)
      }
    ];
    setMessages(dummyMessages);
  }, []);

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      type: "human",
      content: inputText,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    setInputText("");
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        console.log('Recording completed, blob size:', audioBlob.size);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const humanMessages = messages.filter(m => m.type === "human");
  const generativeMessages = messages.filter(m => m.type === "generative");

  const HumanArea = () => (
    <div className="flex flex-col h-full bg-background border-r border-border">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-medium">Conversation</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {humanMessages.map((message) => (
          <div key={message.id} className="bg-muted rounded-lg p-3">
            <p className="text-sm text-muted-foreground mb-1">
              {message.timestamp.toLocaleTimeString()}
            </p>
            <p>{message.content}</p>
          </div>
        ))}
      </div>
      <div className="p-4 border-t border-border">
        <div className="flex gap-2 mb-2">
          <input
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <Button onClick={handleSendMessage} size="sm">
            Send
          </Button>
        </div>
        <div className="flex gap-2">
          <Button
            variant={isRecording ? "destructive" : "outline"}
            size="sm"
            onClick={isRecording ? stopRecording : startRecording}
          >
            {isRecording ? "Stop" : "Record"}
          </Button>
          <div className="md:hidden flex-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowGenerative(!showGenerative)}
              className="w-full"
            >
              {showGenerative ? "← Conversation" : "View Output →"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  const GenerativeArea = () => (
    <div className="flex flex-col h-full bg-background">
      <div className="p-4 border-b border-border flex justify-between items-center">
        <h2 className="text-lg font-medium">Generated Output</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSettings(prev => ({ ...prev, generativeOnRight: !prev.generativeOnRight }))}
        >
          Switch Sides
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {generativeMessages.map((message) => (
          <div key={message.id} className="bg-secondary/10 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-2">
              {message.timestamp.toLocaleTimeString()}
            </p>
            <pre className="whitespace-pre-wrap text-sm bg-background border border-border rounded p-3 overflow-x-auto">
              {message.content}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Mobile View */}
      <div className="md:hidden h-full">
        <div className={`h-full transition-transform duration-300 ${showGenerative ? '-translate-x-full' : 'translate-x-0'}`}>
          <HumanArea />
        </div>
        <div className={`absolute inset-0 transition-transform duration-300 ${showGenerative ? 'translate-x-0' : 'translate-x-full'}`}>
          <GenerativeArea />
        </div>
      </div>

      {/* Desktop View */}
      <div className="hidden md:flex h-full">
        {settings.generativeOnRight ? (
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

export default App;
