import { useState, useRef } from "react";
import type { RagResponse } from "../api/types";
import { api, streamChat } from "../api/client";

interface Props {
  hasDocuments: boolean;
}

export default function ChatPanel({ hasDocuments }: Props) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [result, setResult] = useState<RagResponse | null>(null);
  const [error, setError] = useState("");
  const abortRef = useRef(false);

  const handleAsk = async () => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError("");
    setResult(null);
    setStreamText("");
    abortRef.current = false;

    try {
      // First get the full RAG response (with evidence, citations, etc.)
      const ragResult = await api.post<RagResponse>("/chat", { query: query.trim() });
      setResult(ragResult);

      // Then stream the answer if we have evidence and the answer is grounded
      if (ragResult.answer && ragResult.evidence.length > 0 && !ragResult.abstained) {
        setStreaming(true);
        setStreamText("");

        await streamChat(
          {
            query: query.trim(),
            evidence: ragResult.evidence,
            temperature: 0.0,
          },
          (chunk) => {
            if (!abortRef.current) {
              setStreamText((prev) => prev + chunk);
            }
          },
          () => setStreaming(false),
          (msg) => {
            setError(msg);
            setStreaming(false);
          },
        );
      }
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "message" in err
          ? (err as { message: string }).message
          : "Failed to get answer";
      setError(msg);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const displayAnswer = streamText || result?.answer;
  const uniquePages = result?.citations
    ? [...new Set(result.citations.map((c) => c.page_number))].sort((a, b) => a - b)
    : [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Ask your documents</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          {hasDocuments
            ? "Ask a question and get answers grounded in your uploaded documents"
            : "Upload a document first to start asking questions"}
        </p>
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            disabled={!hasDocuments || loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:text-gray-400"
          />
          <button
            onClick={handleAsk}
            disabled={!query.trim() || !hasDocuments || loading}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Thinking...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Ask
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {!result && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm">Ask a question about your documents</p>
            <p className="text-gray-400 text-xs mt-1">Press Enter or click Ask</p>
          </div>
        )}

        {loading && !result && (
          <div className="flex items-center gap-3 text-gray-500">
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="text-sm">Analyzing your question...</span>
          </div>
        )}

        {result && (
          <div className="space-y-6">
            {/* Query Analysis */}
            {(result.query_analysis.expanded_queries.length > 0 || result.query_analysis.sub_queries.length > 0) && (
              <details className="group">
                <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                  <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Query Analysis
                </summary>
                <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs text-gray-600 space-y-1">
                  {result.query_analysis.expanded_queries.map((q, i) => (
                    <p key={i}>Expanded: {q}</p>
                  ))}
                  {result.query_analysis.sub_queries.map((q, i) => (
                    <p key={i}>Sub-query: {q}</p>
                  ))}
                </div>
              </details>
            )}

            {/* Evidence / Verdict */}
            {result.evidence.length > 0 && (
              <details className="group">
                <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                  <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Evidence ({result.evidence.length} chunks) — Confidence: {(result.verdict.confidence_score * 100).toFixed(0)}%
                </summary>
                <div className="mt-2 space-y-2">
                  {result.evidence.slice(0, 5).map((chunk, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg text-xs">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-700">Page {chunk.page_number}</span>
                        {chunk.score > 0 && (
                          <span className="text-gray-400">Score: {chunk.score.toFixed(3)}</span>
                        )}
                      </div>
                      <p className="text-gray-600 line-clamp-2">{chunk.content}</p>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* Abstention */}
            {result.abstained && (
              <div className="p-5 rounded-xl bg-amber-50 border border-amber-200">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-amber-800">Unable to answer</p>
                    <p className="text-sm text-amber-700 mt-1">{result.abstention_reason}</p>
                    {result.abstention_suggestion && (
                      <p className="text-xs text-amber-600 mt-2">{result.abstention_suggestion}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Answer */}
            {displayAnswer && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2">Answer</h3>
                <div className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm">
                  <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                    {displayAnswer}
                    {streaming && (
                      <span className="inline-block w-0.5 h-4 bg-indigo-500 ml-0.5 animate-pulse" />
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Citations */}
            {result.citations.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-2">Sources</h3>
                <div className="flex flex-wrap gap-2">
                  {result.citations.map((cit, i) => (
                    <div
                      key={i}
                      className="group/cit relative px-3 py-1.5 bg-indigo-50 border border-indigo-200 rounded-lg text-xs font-medium text-indigo-700 hover:bg-indigo-100 transition-colors cursor-default"
                    >
                      Page {cit.page_number}
                      {cit.confidence !== null && (
                        <span className="text-indigo-400 ml-1">
                          ({(cit.confidence * 100).toFixed(0)}%)
                        </span>
                      )}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover/cit:opacity-100 transition-opacity pointer-events-none z-10">
                        <p className="line-clamp-3">{cit.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
                {/* Unique page tabs */}
                {uniquePages.length > 0 && (
                  <div className="flex gap-2 mt-3">
                    {uniquePages.map((page) => (
                      <span
                        key={page}
                        className="px-2 py-1 bg-gray-100 text-gray-600 rounded-md text-xs"
                      >
                        Page {page}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Verification */}
            {result.verification && (
              <details className="group">
                <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                  <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Verification
                  <span className={`ml-1 ${result.verification.supported ? "text-emerald-600" : "text-red-600"}`}>
                    {result.verification.supported ? "Passed" : "Failed"}
                  </span>
                </summary>
                <div className="mt-2 p-3 bg-gray-50 rounded-lg text-xs text-gray-600 space-y-1">
                  <p>Supported: {result.verification.supported ? "Yes" : "No"}</p>
                  <p>Citations correct: {result.verification.citations_correct ? "Yes" : "No"}</p>
                  {result.verification.explanation && <p>{result.verification.explanation}</p>}
                </div>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
