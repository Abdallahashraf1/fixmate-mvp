// lib/types.ts
export interface Session {
  session_id: string;
  created_at: string;
  summary: string;
  user_id: string;
}

export interface ImageAttachment {
  id: string;
  page: number;
  source: string;
  data: string;
}

export interface SourceChunk {
  chunk_id: string;
  text: string;
  source: string;
  page: number;
  rrf_score: number;
  dense_rank?: number | null;
  bm25_rank?: number | null;
  dense_score?: number | null;
  bm25_score?: number | null;
  metadata?: Record<string, unknown>;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  isLoading?: boolean;
  is_ar?: boolean;
  timestamp?: string;
  images?: ImageAttachment[];
  sources?: SourceChunk[];
  guardrails?: Record<string, unknown>;
}

export interface ChatRequest {
  session_id?: string;
  user_id: string;
  role: string;
  make: string;
  model: string;
  query: string;
}

export interface ChatResponse {
  assistant_text: string;
  images: ImageAttachment[];
  session_id?: string;
  sources?: SourceChunk[];
  guardrails?: Record<string, unknown>;
}
