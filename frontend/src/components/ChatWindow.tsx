import { useCallback, useRef, useEffect, useState } from "react";
import { askQuestion, getConversation } from "../api";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import { useAuth } from "../AuthContext";

interface ChatWindowProps {
    conversationId: string | null;
    onConversationChange: (id: string | null) => void;
}

export default function ChatWindow({ conversationId, onConversationChange }: ChatWindowProps) {
    const { isAuthenticated } = useAuth();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Load conversation history when conversationId changes
    useEffect(() => {
        if (conversationId && isAuthenticated) {
            loadConversationHistory(conversationId);
        } else {
            setMessages([]);
        }
    }, [conversationId, isAuthenticated]);

    const loadConversationHistory = async (convId: string) => {
        setLoadingHistory(true);
        try {
            const data = await getConversation(convId);
            const loadedMessages: ChatMessage[] = data.messages.map((msg) => ({
                id: msg.id,
                role: msg.role === "user" ? "user" : "bot",
                content: msg.content,
                sources: msg.sources,
                timestamp: new Date(msg.created_at),
            }));
            setMessages(loadedMessages);
        } catch (error) {
            console.error("Failed to load conversation:", error);
            setMessages([]);
        } finally {
            setLoadingHistory(false);
        }
    };

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = useCallback(async (text: string) => {
        const userMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const res = await askQuestion({
                query: text,
                conversation_id: conversationId || undefined,
            });

            // Update conversation ID if a new one was created
            if (res.conversation_id && res.conversation_id !== conversationId) {
                onConversationChange(res.conversation_id);
            }

            const botMsg: ChatMessage = {
                id: crypto.randomUUID(),
                role: "bot",
                content: res.answer,
                sources: res.sources,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, botMsg]);
        } catch (e: unknown) {
            const errMsg: ChatMessage = {
                id: crypto.randomUUID(),
                role: "bot",
                content: `Error: ${e instanceof Error ? e.message : "Something went wrong"}`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errMsg]);
        } finally {
            setLoading(false);
        }
    }, [conversationId, onConversationChange]);

    return (
        <div className="flex flex-col h-full">
            <h2 className="text-lg font-semibold text-gray-800 mb-3 shrink-0">
                Chat
                {conversationId && (
                    <button
                        onClick={() => onConversationChange(null)}
                        className="ml-2 text-sm font-normal text-blue-600 hover:text-blue-700"
                    >
                        Start New
                    </button>
                )}
            </h2>

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto mb-4 pr-1">
                {loadingHistory ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        Loading conversation...
                    </div>
                ) : messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                        Upload a document and ask a question to get started.
                    </div>
                ) : (
                    messages.map((m) => (
                        <MessageBubble key={m.id} message={m} />
                    ))
                )}
                {loading && (
                    <div className="flex justify-start mb-3">
                        <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="shrink-0">
                <ChatInput onSend={handleSend} disabled={loading || loadingHistory} />
            </div>
        </div>
    );
}
