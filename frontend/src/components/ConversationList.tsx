import { useState, useEffect } from "react";
import { useAuth } from "../AuthContext";
import { getConversations, deleteConversation } from "../api";
import type { Conversation } from "../types";

interface ConversationListProps {
    currentConversationId: string | null;
    onSelectConversation: (conversationId: string | null) => void;
}

export default function ConversationList({
    currentConversationId,
    onSelectConversation,
}: ConversationListProps) {
    const { isAuthenticated } = useAuth();
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (isAuthenticated) {
            loadConversations();
        } else {
            setConversations([]);
        }
    }, [isAuthenticated]);

    const loadConversations = async () => {
        setIsLoading(true);
        try {
            const data = await getConversations();
            setConversations(data.conversations);
        } catch (error) {
            console.error("Failed to load conversations:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (e: React.MouseEvent, conversationId: string) => {
        e.stopPropagation();
        if (!confirm("Delete this conversation?")) return;

        try {
            await deleteConversation(conversationId);
            setConversations((prev) => prev.filter((c) => c.id !== conversationId));
            if (currentConversationId === conversationId) {
                onSelectConversation(null);
            }
        } catch (error) {
            console.error("Failed to delete conversation:", error);
        }
    };

    if (!isAuthenticated) {
        return (
            <div className="text-sm text-gray-500 text-center py-4">
                Login to save your conversations
            </div>
        );
    }

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-700">Conversations</h3>
                <button
                    onClick={() => onSelectConversation(null)}
                    className="text-xs text-blue-600 hover:text-blue-700"
                >
                    + New
                </button>
            </div>

            {isLoading ? (
                <div className="text-sm text-gray-500 text-center py-2">Loading...</div>
            ) : conversations.length === 0 ? (
                <div className="text-sm text-gray-500 text-center py-2">
                    No conversations yet
                </div>
            ) : (
                <div className="space-y-1 max-h-60 overflow-y-auto">
                    {conversations.map((conv) => (
                        <div
                            key={conv.id}
                            onClick={() => onSelectConversation(conv.id)}
                            className={`flex items-center justify-between p-2 rounded cursor-pointer group ${currentConversationId === conv.id
                                    ? "bg-blue-100 text-blue-700"
                                    : "hover:bg-gray-100"
                                }`}
                        >
                            <span className="text-sm truncate flex-1">{conv.title}</span>
                            <button
                                onClick={(e) => handleDelete(e, conv.id)}
                                className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
