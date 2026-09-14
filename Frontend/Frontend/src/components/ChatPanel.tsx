import { useState, useRef } from "react";
import Markdown from "react-markdown";
import type { RagResponse, SourceChunk } from "../api/types";
import { api, streamChat } from "../api/client";

interface Props {
  hasDocuments: boolean;
}

type StepState = "pending" | "active" | "done" | "skipped";

function Spinner({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={`${className} animate-spin`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function PipelineTracker({
  steps,
}: {
  steps: { label: string; state: StepState; detail?: string }[];
}) {
  return (
    <div className="border border-[#E2E4E8] rounded-xl bg-white px-5 py-4 shadow-sm animate-fade-in">
      <div className="flex items-stretch">
        {steps.map((step, i) => (
          <div key={step.label} className="flex-1 flex items-center min-w-0">
            <div className="flex flex-col gap-1.5 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
                    step.state === "done"
                      ? "bg-[#0B5D52] shadow-[0_0_8px_rgba(11,93,82,0.3)]"
                      : step.state === "active"
                      ? "bg-[#B9862F] shadow-[0_0_8px_rgba(185,134,47,0.3)]"
                      : step.state === "skipped"
                      ? "bg-[#EEF0F2] border border-[#D8DBE0]"
                      : "bg-[#EEF0F2] border border-[#E2E4E8]"
                  }`}
                >
                  {step.state === "done" && (
                    <svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="white">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {step.state === "active" && <Spinner className="w-3 h-3 text-white" />}
                </span>
                <span
                  className={`text-[12px] font-medium truncate transition-colors duration-200 ${
                    step.state === "pending" || step.state === "skipped" ? "text-[#8B93A1]" : "text-[#14181F]"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              <span className="text-[11px] font-['IBM_Plex_Mono',monospace] text-[#8B93A1] pl-[28px] truncate">
                {step.detail ?? "\u00A0"}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`h-px flex-1 mx-4 transition-colors duration-300 ${step.state === "done" ? "bg-[#0B5D52]/30" : "bg-[#E2E4E8]"}`} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

const SUGGESTED_QUESTIONS = [
  "What are the main findings?",
  "Summarize the key points",
  "What methodology was used?",
];

export default function ChatPanel({ hasDocuments }: Props) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [result, setResult] = useState<RagResponse | null>(null);
  const [error, setError] = useState("");
  const [showSources, setShowSources] = useState(false);
  const abortRef = useRef(false);

  const handleAsk = async (question?: string) => {
    const q = question || query.trim();
    if (!q || loading) return;
    setQuery(q);
    setLoading(true);
    setError("");
    setResult(null);
    setStreamText("");
    abortRef.current = false;

    try {
      const ragResult = await api.post<RagResponse>("/chat", { query: q });
      setResult(ragResult);

      if (ragResult.answer && ragResult.sources.length > 0 && !ragResult.abstained) {
        setStreaming(true);
        setStreamText("");

        const evidenceChunks = ragResult.sources.map((s: SourceChunk, i: number) => ({
          chunk_id: i,
          document_id: s.document_id,
          content: s.content,
          page_number: s.page_number,
          page_numbers: [s.page_number],
          content_type: "text",
          metadata: {},
          score: s.score,
          rerank_score: null,
        }));

        await streamChat(
          { query: q, evidence: evidenceChunks, temperature: 0.0 },
          (chunk) => {
            if (!abortRef.current) setStreamText((prev) => prev + chunk);
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

  const pipelineSteps: { label: string; state: StepState; detail?: string }[] = result
    ? [
        { label: "Hybrid retrieval", state: "done", detail: `${result.sources.length} chunks` },
        {
          label: "Generation",
          state: streaming ? "active" : result.abstained ? "skipped" : "done",
          detail: result.abstained ? "abstained" : streaming ? "streaming…" : "complete",
        },
      ]
    : loading
    ? [
        { label: "Hybrid retrieval", state: "active" },
        { label: "Generation", state: "pending" },
      ]
    : [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#E2E4E8] bg-white flex-shrink-0">
        <h2 className="text-[15px] font-semibold text-[#14181F]">Ask your documents</h2>
        <p className="text-[13px] text-[#8B93A1] mt-0.5">
          {hasDocuments
            ? "Grounded answers with source citations — verified before display"
            : "Upload a document first to start asking questions"}
        </p>
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-b border-[#E2E4E8] bg-[#FAFBFB] flex-shrink-0">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasDocuments ? "Ask a question…" : "Upload documents to get started"}
              disabled={!hasDocuments || loading}
              className="w-full px-4 py-3 rounded-xl border border-[#D8DBE0] bg-white text-[13px] text-[#14181F] placeholder:text-[#B4BAC2] focus:outline-none focus:ring-2 focus:ring-[#0B5D52]/20 focus:border-[#0B5D52] disabled:bg-[#F0F1F3] disabled:text-[#B4BAC2] transition-all duration-200 shadow-sm"
            />
            {query && !loading && (
              <button
                onClick={() => { setQuery(""); setResult(null); setError(""); }}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-md text-[#B4BAC2] hover:text-[#5B6472] hover:bg-[#EEF0F2] transition-colors"
              >
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <button
            onClick={() => handleAsk()}
            disabled={!query.trim() || !hasDocuments || loading}
            className="px-5 py-3 bg-[#0B5D52] hover:bg-[#0A4F46] disabled:bg-[#B7CCC8] text-white rounded-xl text-[13px] font-medium transition-all duration-200 flex items-center gap-2 flex-shrink-0 shadow-sm hover:shadow-md disabled:shadow-none active:scale-[0.98]"
          >
            {loading ? (
              <>
                <Spinner />
                Thinking…
              </>
            ) : (
              <>
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Ask
              </>
            )}
          </button>
        </div>
        {hasDocuments && !result && !loading && (
          <div className="flex items-center gap-2 mt-3">
            <span className="text-[11px] text-[#B4BAC2]">Try:</span>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => handleAsk(q)}
                className="text-[11px] text-[#5B6472] bg-white border border-[#E2E4E8] px-2.5 py-1 rounded-full hover:border-[#0B5D52]/30 hover:text-[#0B5D52] hover:bg-[#F1F7F6] transition-all duration-200"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-[#FBEAE6] border border-[#F0CCC3] text-[#8A2F1C] text-[13px] flex items-start gap-3 animate-slide-up">
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="flex-shrink-0 mt-0.5">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {!result && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-[#EEF0F2] to-[#E2E4E8] rounded-2xl flex items-center justify-center mb-5 shadow-inner">
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="text-[#8B93A1]">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-[#5B6472] text-[14px] font-medium">Ask a question about your documents</p>
            <p className="text-[#B4BAC2] text-[12px] mt-1.5">Press Enter or click Ask to get started</p>
          </div>
        )}

        {(loading || result) && (
          <div className="mb-6 animate-fade-in">
            <PipelineTracker steps={pipelineSteps} />
          </div>
        )}

        {result && (
          <div className="space-y-6">
            {/* Sources */}
            {result.sources.length > 0 && (
              <div className="animate-slide-up">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center gap-2 text-[12px] font-medium text-[#5B6472] hover:text-[#14181F] transition-colors mb-2"
                >
                  <svg
                    width="12"
                    height="12"
                    className={`transition-transform duration-200 ${showSources ? "rotate-90" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Retrieved evidence
                  <span className="text-[#8B93A1] font-normal">({result.sources.length} chunks)</span>
                </button>
                {showSources && (
                  <div className="space-y-2 mt-2 animate-slide-up">
                    {result.sources.slice(0, 5).map((chunk, i) => (
                      <div
                        key={i}
                        className="p-3.5 bg-[#FAFBFB] border border-[#E2E4E8] rounded-xl hover:border-[#D8DBE0] transition-colors"
                      >
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="text-[11px] font-medium text-[#14181F] bg-[#EEF0F2] px-2 py-0.5 rounded-md">
                            Page {chunk.page_number}
                          </span>
                          {chunk.score > 0 && (
                            <span className="text-[11px] font-['IBM_Plex_Mono',monospace] text-[#8B93A1]">
                              {chunk.score.toFixed(3)}
                            </span>
                          )}
                        </div>
                        <p className="text-[12px] text-[#5B6472] line-clamp-2 leading-relaxed">{chunk.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Abstention */}
            {result.abstained && (
              <div className="p-4 rounded-xl bg-[#FBF3E4] border border-[#EBD6A6] flex gap-3 animate-slide-up">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-[#F2E3BC]">
                  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="text-[#8A6415]">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <p className="text-[13px] font-medium text-[#5C4310]">Unable to answer</p>
                  <p className="text-[13px] text-[#7A5A16] mt-0.5 leading-relaxed">{result.abstention_reason}</p>
                  {result.abstention_suggestion && (
                    <p className="text-[12px] text-[#8A6415] mt-2 italic">{result.abstention_suggestion}</p>
                  )}
                </div>
              </div>
            )}

            {/* Answer */}
            {displayAnswer && (
              <div className="animate-slide-up">
                <h3 className="text-[12px] font-semibold text-[#5B6472] mb-3 uppercase tracking-wider">Answer</h3>
                <div className="pl-4 border-l-2 border-[#0B5D52] py-1.5">
                  <div className="markdown-body text-[14px] leading-[1.75] text-[#14181F]">
                    <Markdown>{displayAnswer}</Markdown>
                    {streaming && (
                      <span className="inline-block w-0.5 h-4 bg-[#0B5D52] ml-0.5 animate-pulse align-middle" />
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Citations */}
            {result.citations.length > 0 && (
              <div className="animate-slide-up">
                <h3 className="text-[12px] font-semibold text-[#5B6472] mb-3 uppercase tracking-wider">
                  Sources
                  {uniquePages.length > 0 && (
                    <span className="font-normal text-[#8B93A1] normal-case"> · pages {uniquePages.join(", ")}</span>
                  )}
                </h3>
                <div className="border border-[#E2E4E8] rounded-xl overflow-hidden">
                  {result.citations.map((cit, i) => (
                    <div
                      key={i}
                      className={`flex gap-3 px-4 py-3 hover:bg-[#FAFBFB] transition-colors ${
                        i > 0 ? "border-t border-[#E2E4E8]" : ""
                      }`}
                    >
                      <span className="text-[11px] font-['IBM_Plex_Mono',monospace] text-[#0B5D52] bg-[#F1F7F6] w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 font-medium">
                        {i + 1}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[12px] font-medium text-[#14181F]">Page {cit.page_number}</span>
                          {cit.confidence !== null && (
                            <span className="text-[11px] font-['IBM_Plex_Mono',monospace] text-[#0B5D52] bg-[#F1F7F6] px-1.5 py-0.5 rounded-md">
                              {(cit.confidence * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                        <p className="text-[12px] text-[#5B6472] line-clamp-2 leading-relaxed">{cit.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
