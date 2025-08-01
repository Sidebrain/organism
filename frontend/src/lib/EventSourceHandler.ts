interface ChoiceDelta {
  content?: string;
  role?: string;
}

interface Choice {
  index: number;
  delta: ChoiceDelta;
  finishReason?: string;
}

export interface StreamingResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Choice[];
}

export interface EventSourceConfig {
  url: string;
  onDelta?: (content: string, messageId?: string) => void;
  onDone?: (messageId?: string) => void;
  onError?: (error: string) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export class EventSourceHandler {
  private eventSource: EventSource | null = null;
  private config: EventSourceConfig;

  constructor(config: EventSourceConfig) {
    this.config = config;
  }

  public connect(): void {
    if (this.eventSource) {
      this.disconnect();
    }

    this.eventSource = new EventSource(this.config.url);
    this.setupEventListeners();
  }

  public disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.config.onConnectionChange?.(false);
    }
  }

  public isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN;
  }

  private setupEventListeners(): void {
    if (!this.eventSource) {
      return;
    }

    this.eventSource.addEventListener("message", (event) => {
      try {
        const data: StreamingResponse = JSON.parse(event.data);

        const choice = data.choices[0];
        if (choice && choice.delta.content) {
          this.config.onDelta?.(choice.delta.content, data.id);
        }

        if (choice && choice.finishReason === "stop") {
          this.config.onDone?.(data.id);
        }
      } catch (error) {
        console.error("Message event parsing error:", error);
      }
    });

    this.eventSource.addEventListener("error", () => {
      this.config.onError?.("Connection error");
    });

    this.eventSource.addEventListener("open", () => {
      this.config.onConnectionChange?.(true);
    });
  }
}
