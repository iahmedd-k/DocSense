import { useEffect, useState, useRef } from "react";
import type { Document } from "../api/types";
import { api } from "../api/client";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS: Record<Document["status"], { dot: string; label: string; pulse?: boolean; bg: string }> = {
  completed: { dot: "bg-[#0B7A4B]", label: "Processed", bg: "bg-[#F1F7F6]" },
  processing: { dot: "bg-[#B9862F]", label: "Processing", pulse: true, bg: "bg-[#FBF3E4]" },
  uploaded: { dot: "bg-[#5B6472]", label: "Queued", bg: "bg-[#EEF0F2]" },
  failed: { dot: "bg-[#B4432E]", label: "Failed", bg: "bg-[#FBEAE6]" },
};

function StatusDot({ status }: { status: Document["status"] }) {
  const s = STATUS[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-[10px] font-medium px-1.5 py-0.5 rounded-md ${s.bg} ${
      status === "processing" ? "text-[#8A6415]" : status === "completed" ? "text-[#0B7A4B]" : status === "failed" ? "text-[#8A2F1C]" : "text-[#5B6472]"
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot} ${s.pulse ? "animate-pulse" : ""}`} />
      {s.label}
    </span>
  );
}

interface Props {
  selectedId: number | null;
  onSelect: (doc: Document) => void;
  onCountChange?: (count: number) => void;
}

export default function DocumentList({ selectedId, onSelect, onCountChange }: Props) {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const fileInput = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const fetchDocs = async () => {
    try {
      const data = await api.get<Document[]>("/documents");
      setDocs(data);
      onCountChange?.(data.length);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await api.post<Document>("/documents", formData);
      await fetchDocs();
    } catch {
      // could show toast
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this document?")) return;
    try {
      await api.delete(`/documents/${id}`);
      setDocs((prev) => prev.filter((d) => d.id !== id));
      if (selectedId === id) onSelect(null as unknown as Document);
    } catch {
      // silent
    }
  };

  return (
    <div className="flex flex-col h-full">
      <input ref={fileInput} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
      <button
        onClick={() => fileInput.current?.click()}
        disabled={uploading}
        className="mb-3 inline-flex items-center justify-center gap-2 px-3 py-2.5 bg-[#0B5D52] hover:bg-[#0A4F46] disabled:bg-[#B7CCC8] text-white rounded-lg text-[12px] font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0B5D52]/40 shadow-sm hover:shadow-md disabled:shadow-none active:scale-[0.98]"
      >
        {uploading ? (
          <>
            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Uploading…
          </>
        ) : (
          <>
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M12 4v16m8-8H4" />
            </svg>
            Upload PDF
          </>
        )}
      </button>

      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#0B5D52] animate-pulse" />
            <div className="w-1.5 h-1.5 rounded-full bg-[#0B5D52] animate-pulse" style={{ animationDelay: "0.2s" }} />
            <div className="w-1.5 h-1.5 rounded-full bg-[#0B5D52] animate-pulse" style={{ animationDelay: "0.4s" }} />
          </div>
          <span className="text-[12px] text-[#8B93A1]">Loading documents…</span>
        </div>
      ) : docs.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
          <div className="w-12 h-12 bg-gradient-to-br from-[#EEF0F2] to-[#E2E4E8] rounded-xl flex items-center justify-center mb-3 shadow-inner">
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="text-[#8B93A1]">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-[#5B6472] text-[13px] font-medium mb-1">No documents yet</p>
          <p className="text-[#8B93A1] text-[11px] leading-relaxed">Upload a PDF to start<br />indexing and querying</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto -mx-1 scrollbar-thin">
          {docs.map((doc, index) => {
            const selected = selectedId === doc.id;
            return (
              <div
                key={doc.id}
                onClick={() => onSelect(doc)}
                style={{ animationDelay: `${index * 30}ms` }}
                className={`group flex items-start gap-2.5 py-2.5 px-2.5 mx-1 cursor-pointer border-l-2 transition-all duration-150 animate-fade-in ${
                  selected
                    ? "border-l-[#0B5D52] bg-[#F1F7F6] shadow-sm"
                    : "border-l-transparent hover:bg-[#F9FAFA]"
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors duration-200 ${
                  selected ? "bg-[#0B5D52]/10" : "bg-[#FBEAE6]"
                }`}>
                  <svg width="15" height="15" fill="currentColor" viewBox="0 0 24 24" className={selected ? "text-[#0B5D52]" : "text-[#B4432E]"}>
                    <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-[12px] font-medium truncate leading-snug ${
                    selected ? "text-[#0B5D52]" : "text-[#14181F]"
                  }`}>
                    {doc.original_filename}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <StatusDot status={doc.status} />
                    <span className="text-[10px] font-['IBM_Plex_Mono',monospace] text-[#8B93A1]">
                      {formatSize(doc.file_size)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(doc.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-[#8B93A1] hover:text-[#B4432E] hover:bg-[#FBEAE6] transition-all duration-150 flex-shrink-0"
                >
                  <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
