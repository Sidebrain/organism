import { Button } from "./ui/button";
import { useAppContext } from "@/context/AppContext";
export const GenerativeArea = () => {
  const appContext = useAppContext();

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="p-4 border-b border-border flex justify-between items-center">
        <h2 className="text-lg font-medium">Generated Output</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() =>
            appContext.setSettings((prev) => ({
              ...prev,
              generativeOnRight: !prev.generativeOnRight,
            }))
          }
        >
          Switch Sides
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {appContext.generativeMessages.map((message) => (
          <div
            key={message.id}
            className="bg-secondary/10 rounded-lg p-4"
          >
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
};
