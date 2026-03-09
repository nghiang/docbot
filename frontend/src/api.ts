import type {
    UploadResponse,
    PresignResponse,
    TaskStatus,
    AskRequest,
    AskResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    User,
    Conversation,
    ConversationMessage,
    DocumentRecord,
} from "./types";

const API_BASE = "/api";

// Token management
let authToken: string | null = localStorage.getItem("token");

export function setAuthToken(token: string | null) {
    authToken = token;
    if (token) {
        localStorage.setItem("token", token);
    } else {
        localStorage.removeItem("token");
    }
}

export function getAuthToken(): string | null {
    return authToken;
}

async function request<T>(
    url: string,
    options?: RequestInit,
    requireAuth = false
): Promise<T> {
    const headers: Record<string, string> = {
        ...(options?.headers as Record<string, string>),
    };

    if (requireAuth && authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
    }

    const res = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers,
    });

    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed: ${res.status}`);
    }
    return res.json();
}

// ──────────────────────────────────────────────
// Auth API
// ──────────────────────────────────────────────

export async function register(data: RegisterRequest): Promise<User> {
    return request<User>("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
    const response = await request<TokenResponse>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    setAuthToken(response.access_token);
    return response;
}

export async function getMe(): Promise<User> {
    return request<User>("/auth/me", {}, true);
}

export function logout() {
    setAuthToken(null);
}

// ──────────────────────────────────────────────
// Conversation API
// ──────────────────────────────────────────────

export async function getConversations(): Promise<{ conversations: Conversation[] }> {
    return request<{ conversations: Conversation[] }>("/conversations", {}, true);
}

export async function getConversation(
    conversationId: string
): Promise<{ conversation: Conversation; messages: ConversationMessage[] }> {
    return request<{ conversation: Conversation; messages: ConversationMessage[] }>(
        `/conversations/${conversationId}`,
        {},
        true
    );
}

export async function createConversation(
    title?: string
): Promise<{ conversation_id: string }> {
    return request<{ conversation_id: string }>(
        "/conversations",
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title }),
        },
        true
    );
}

export async function deleteConversation(conversationId: string): Promise<void> {
    await request<{ status: string }>(
        `/conversations/${conversationId}`,
        { method: "DELETE" },
        true
    );
}

// ──────────────────────────────────────────────
// Document API
// ──────────────────────────────────────────────

/**
 * Upload a file using presigned URL flow:
 * 1. Get a presigned PUT URL from the backend
 * 2. PUT the file directly to MinIO via the /storage/ proxy
 * 3. Notify the backend to start indexing
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
    // Step 1: Get presigned URL
    const presign = await request<PresignResponse>("/upload/presign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_name: file.name }),
    }, true);

    // Step 2: Upload directly to MinIO via presigned URL
    const putRes = await fetch(presign.upload_url, {
        method: "PUT",
        body: file,
    });
    if (!putRes.ok) {
        throw new Error(`Direct upload failed: ${putRes.status} ${putRes.statusText}`);
    }

    // Step 3: Notify backend that upload is complete → triggers indexing
    return request<UploadResponse>("/upload/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_name: file.name }),
    }, true);
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
    return request<TaskStatus>(`/task/${taskId}`);
}

export async function getDocuments(): Promise<DocumentRecord[]> {
    return request<DocumentRecord[]>("/documents", {}, true);
}

export async function deleteDocument(docId: number): Promise<void> {
    await request<void>(`/documents/${docId}`, { method: "DELETE" }, true);
}

export async function askQuestion(payload: AskRequest): Promise<AskResponse> {
    const isAuthenticated = !!authToken;
    return request<AskResponse>(
        "/ask",
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        },
        isAuthenticated
    );
}
