import type { Message } from "@/context/AppContext";
import type { StreamingResponse } from "./EventSourceHandler";

export const updateMessagesWithStreamData = (
  prevMessages: Message[],
  data: StreamingResponse
): Message[] => {
  const existingMessageIndex = prevMessages.findIndex(
    (msg) => msg.id === data.id
  );

  if (existingMessageIndex !== -1) {
    return prevMessages.map((msg, index) =>
      index === existingMessageIndex
        ? {
            ...msg,
            content: msg.content + data.choices[0].delta.content,
          }
        : msg
    );
  } else {
    const newMessage: Message = {
      id: data.id,
      type: "generative",
      content: data.choices[0].delta.content || "",
      timestamp: new Date(),
    };
    return [...prevMessages, newMessage];
  }
};

export const createHumanMessage = (content: string): Message => {
  return {
    id: Date.now().toString(),
    type: "human",
    content,
    timestamp: new Date(),
  };
};
