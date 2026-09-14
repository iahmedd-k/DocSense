export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Document {
  id: number;
  user_id: number;
  original_filename: string;
  storage_key: string;
  storage_url: string;
  mime_type: string;
  file_size: number;
  status: "uploaded" | "processing" | "completed" | "failed";
  created_at: string;
  updated_at: string;
}

export interface SourceCitation {
  text: string;
  document_id: number;
  page_number: number;
  chunk_id: number | null;
  confidence: number | null;
}

export interface RagResponse {
  query: string;
  answer: string | null;
  citations: SourceCitation[];
  sources: SourceChunk[];
  abstained: boolean;
  abstention_reason: string | null;
  abstention_suggestion: string | null;
  confidence: number | null;
}

export interface SourceChunk {
  document_id: number;
  page_number: number;
  content: string;
  score: number;
}

export interface ApiError {
  status_code: number;
  message: string;
}
