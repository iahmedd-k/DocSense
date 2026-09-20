import { api, streamChat } from "./client";
import type {
  Document,
  DocumentStatusResponse,
  Conversation,
  ConversationDetail,
  ConversationListResponse,
  RagResponse,
  UsageResponse,
} from "./types";

/* ── Documents ──────────────────────────────────────────────────────── */

export async function listDocuments(): Promise<Document[]> {
  return api.get<Document[]>("/documents");
}

export async function uploadDocument(
  file: File,
): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);
  return api.post<Document>("/documents", formData);
}

export async function getDocumentStatus(
  documentId: number,
): Promise<DocumentStatusResponse> {
  return api.get<DocumentStatusResponse>(`/documents/${documentId}/status`);
}

export async function deleteDocument(documentId: number): Promise<void> {
  return api.delete<void>(`/documents/${documentId}`);
}

/* ── Conversations ──────────────────────────────────────────────────── */

export async function listConversations(
  offset = 0,
  limit = 50,
): Promise<ConversationListResponse> {
  return api.get<ConversationListResponse>(
    `/conversations?offset=${offset}&limit=${limit}`,
  );
}

export async function createConversation(
  title?: string,
  documentIds?: number[],
): Promise<Conversation> {
  return api.post<Conversation>("/conversations", {
    title: title || "New Conversation",
    document_ids: documentIds || null,
  });
}

export async function getConversation(
  conversationId: number,
): Promise<ConversationDetail> {
  return api.get<ConversationDetail>(`/conversations/${conversationId}`);
}

export async function updateConversationTitle(
  conversationId: number,
  title: string,
): Promise<Conversation> {
  return api.patch<Conversation>(`/conversations/${conversationId}`, {
    title,
  });
}

export async function deleteConversation(
  conversationId: number,
): Promise<void> {
  return api.delete<void>(`/conversations/${conversationId}`);
}

/* ── Chat / RAG ─────────────────────────────────────────────────────── */

export interface ChatRequest {
  query: string;
  conversation_id?: number | null;
  document_ids?: number[] | null;
  top_k?: number;
}

export async function sendChat(request: ChatRequest): Promise<RagResponse> {
  return api.post<RagResponse>("/chat", request);
}

export function sendChatStream(
  body: { query: string; evidence: unknown[]; temperature?: number },
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (msg: string) => void,
) {
  return streamChat(body, onChunk, onDone, onError);
}

/* ── Usage ──────────────────────────────────────────────────────────── */

export async function getUsage(): Promise<UsageResponse> {
  return api.get<UsageResponse>("/usage");
}
