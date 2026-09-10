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

export interface ChunkResult {
  chunk_id: number;
  document_id: number;
  content: string;
  page_number: number;
  page_numbers: number[];
  content_type: string;
  metadata: Record<string, unknown>;
  score: number;
  rerank_score: number | null;
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
  query_analysis: {
    original_query: string;
    expanded_queries: string[];
    sub_queries: string[];
    rationale: string;
  };
  evidence: ChunkResult[];
  verdict: {
    sufficient: boolean;
    confidence_score: number;
    reason: string;
    missing_information: string[];
  };
  answer: string | null;
  citations: SourceCitation[];
  verification: {
    supported: boolean;
    citations_correct: boolean;
    issues: { citation_text: string; claimed_document_id: number; claimed_page: number; issue: string }[];
    explanation: string;
  } | null;
  abstained: boolean;
  abstention_reason: string | null;
  abstention_suggestion: string | null;
  corrective_queries: string[];
  corrective_attempts: number;
  revision_attempts: number;
}

export interface ApiError {
  status_code: number;
  message: string;
}
