import { useRecorder } from "@/hooks/useRecorder";
import { Button } from "./ui/button";
import { useAppContext } from "@/context/AppContext";

export const HumanArea = () => {
  const { isRecording, startRecording, stopRecording } = useRecorder();
  const appContext = useAppContext();

  return (
    <div className="flex flex-col h-full bg-background border-r border-border">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-medium">Conversation</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {appContext.humanMessages.map((message) => (
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
            value={appContext.inputText}
            onChange={(e) => appContext.setInputText(e.target.value)}
            onKeyPress={(e) =>
              e.key === "Enter" && appContext.handleSendMessage()
            }
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <Button onClick={appContext.handleSendMessage} size="sm">
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
              onClick={() =>
                appContext.setShowGenerative(!appContext.showGenerative)
              }
              className="w-full"
            >
              {appContext.showGenerative
                ? "← Conversation"
                : "View Output →"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
