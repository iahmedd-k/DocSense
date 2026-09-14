import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import DocumentList from "../components/DocumentList";
import ChatPanel from "../components/ChatPanel";
import type { Document } from "../api/types";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [docCount, setDocCount] = useState(0);

  return (
    <div className="h-screen flex bg-[#F6F7F8] text-[#14181F] font-['IBM_Plex_Sans',sans-serif]">
      {/* Sidebar */}
      <aside className="w-72 bg-white border-r border-[#E2E4E8] flex flex-col shadow-[1px_0_3px_rgba(0,0,0,0.04)]">
        {/* Logo */}
        <div className="h-16 px-5 flex items-center gap-3 border-b border-[#E2E4E8] flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-[#0B5D52] to-[#0A4F46] rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="white">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="text-[15px] font-semibold leading-tight tracking-tight text-[#14181F]">DocSense</p>
            <p className="text-[11px] text-[#8B93A1] leading-tight mt-0.5">Hybrid search · reranking</p>
          </div>
        </div>

        {/* Documents */}
        <div className="flex-1 overflow-hidden flex flex-col px-4 pt-4 pb-2">
          <div className="flex items-center justify-between px-1 mb-3">
            <h2 className="text-[12px] font-semibold text-[#5B6472] uppercase tracking-wider">Documents</h2>
            <span className="text-[11px] font-['IBM_Plex_Mono',monospace] text-[#5B6472] bg-[#EEF0F2] px-2 py-0.5 rounded-md font-medium">
              {docCount}
            </span>
          </div>
          <div className="flex-1 overflow-hidden">
            <DocumentList
              selectedId={selectedDoc?.id ?? null}
              onSelect={setSelectedDoc}
              onCountChange={setDocCount}
            />
          </div>
        </div>

        {/* User */}
        <div className="px-4 py-3 border-t border-[#E2E4E8] flex-shrink-0 bg-[#FAFBFB]">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#DDEDE9] to-[#C8E0DB] flex items-center justify-center flex-shrink-0 ring-2 ring-white shadow-sm">
                <span className="text-[12px] font-semibold text-[#0B5D52]">
                  {user?.first_name?.[0]}
                  {user?.last_name?.[0]}
                </span>
              </div>
              <div className="min-w-0">
                <p className="text-[13px] font-medium text-[#14181F] truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-[11px] text-[#8B93A1] truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 rounded-lg text-[#8B93A1] hover:text-[#B4432E] hover:bg-[#FBEAE6] transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0B5D52]/40"
              title="Sign out"
            >
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Context bar */}
        <div className="h-14 px-6 flex items-center justify-between border-b border-[#E2E4E8] bg-white flex-shrink-0 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
          <div className="min-w-0">
            <p className="text-[13px] font-medium text-[#14181F] truncate">
              {selectedDoc ? selectedDoc.original_filename : "All documents"}
            </p>
            <p className="text-[11px] text-[#8B93A1]">
              {docCount} document{docCount !== 1 ? "s" : ""} indexed
            </p>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-[#5B6472] flex-shrink-0 bg-[#FAFBFB] px-3 py-1.5 rounded-full border border-[#E2E4E8]">
            <span className={`w-2 h-2 rounded-full transition-colors duration-300 ${docCount > 0 ? "bg-[#0B7A4B] shadow-[0_0_6px_rgba(11,122,75,0.4)]" : "bg-[#C7CCD3]"}`} />
            <span className="font-medium">{docCount > 0 ? "Ready" : "No documents"}</span>
          </div>
        </div>

        <ChatPanel hasDocuments={docCount > 0} />
      </main>
    </div>
  );
}
