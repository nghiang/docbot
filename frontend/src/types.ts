// API response and request types

export interface UploadResponse {
    message: string;
    file_name: string;
    task_id: string;
}

export interface PresignResponse {
    upload_url: string;
    file_name: string;
}

export interface TaskStatus {
    task_id: string;
    status: "PENDING" | "STARTED" | "PROGRESS" | "SUCCESS" | "FAILURE" | "RETRY";
    result?: Record<string, unknown>;
    progress?: {
        step?: string;
        detail?: string;
        percent?: number;
    };
}

export interface SearchResult {
    file_name: string;
    page_number: number;
    page_storage_path: string;
    text: string;
    score: number;
}

export interface AskRequest {
    query: string;
    conversation_id?: string;
    top_k?: number;
    files?: string[];
}

export interface AskResponse {
    answer: string;
    sources: {
        file_name: string;
        page_number: number;
        page_storage_path: string;
        score: number;
    }[];
    conversation_id?: string;
}

export interface ChatMessage {
    id: string;
    role: "user" | "bot";
    content: string;
    sources?: AskResponse["sources"];
    timestamp: Date;
}

export interface UploadedFile {
    id?: number;
    fileName: string;
    taskId: string;
    status: TaskStatus["status"];
    progress?: TaskStatus["progress"];
}

export interface DocumentRecord {
    id: number;
    file_name: string;
    file_type: string;
    task_id: string | null;
    status: string;
    created_at: string;
    updated_at: string;
}

// Auth types
export interface User {
    id: number;
    email: string;
    username: string;
    full_name: string | null;
    is_active: boolean;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    username: string;
    password: string;
    full_name?: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
}

// Conversation types
export interface Conversation {
    id: string;
    user_id: number;
    title: string;
    created_at: string;
    updated_at: string;
}

export interface ConversationMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources: AskResponse["sources"];
    created_at: string;
}
