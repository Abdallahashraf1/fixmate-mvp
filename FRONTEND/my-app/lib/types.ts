// lib/types.ts
export interface Session {
  session_id: string;
  created_at: string;
  summary: string;
  user_id: string;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  is_ar?: boolean;
  timestamp?: string;
  images?: { id: string; page: number; source: string; data: string }[];
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
  images: { id: string; page: number; source: string; data: string }[];
}
