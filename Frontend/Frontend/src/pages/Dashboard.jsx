import React, { useState, useRef, useCallback, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import {
  Search,
  SlidersHorizontal,
  Plus,
  Pencil,
  MoreVertical,
  Paperclip,
  ArrowUp,
  ThumbsUp,
  ThumbsDown,
  RotateCw,
  Star,
  UploadCloud,
  FileText,
  FileSpreadsheet,
  FileJson,
  Link as LinkIcon,
  File,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Folder,
  X,
  Database,
  Gauge,
  MessageSquare,
  AlertTriangle,
  Inbox,
  Mail,
  Lock,
  User,
  LogOut,
  ArrowRight,
  Eye,
  EyeOff,
  Type,
  GitMerge,
  Sparkles,
  ShieldCheck,
  Quote,
} from "lucide-react";

import {
  listDocuments,
  uploadDocument,
  deleteDocument,
  getDocumentStatus,
  listConversations,
  createConversation,
  getConversation,
  updateConversationTitle,
  sendChat,
  getUsage,
} from "../api/services";

/* =====================================================================
   SHARED APP SHELL — dummy client-side routing
===================================================================== */

const NAV = [
  { id: "inbox", label: "Query Console", icon: Inbox },
  { id: "sources", label: "Knowledge Sources", icon: Database },
];

/* =====================================================================
   PLANS — Free / Pro quota config
===================================================================== */

const PLANS = {
  free: {
    id: "free",
    name: "Free",
    price: "$0",
    priceSub: "forever",
    queryLimit: 20,
    uploadLimit: 5,
    storageLimitBytes: 500 * 1024 * 1024,
    seats: 1,
    features: ["20 queries / month", "5 indexed sources", "500 MB storage", "1 seat"],
  },
  pro: {
    id: "pro",
    name: "Pro",
    price: "$49",
    priceSub: "/ seat / month",
    queryLimit: Infinity,
    uploadLimit: Infinity,
    storageLimitBytes: 25 * 1024 * 1024 * 1024,
    seats: 10,
    features: ["Unlimited queries", "Unlimited indexed sources", "25 GB storage / seat", "Up to 10 seats", "Priority retrieval latency"],
  },
};

function PlanBadge({ plan, onClick }) {
  const cfg = PLANS[plan];
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 text-[12.5px] font-medium px-3 py-1.5 rounded-lg border transition-colors shrink-0 ${
        plan === "pro" ? "border-indigo-200 bg-indigo-50 text-indigo-700" : "border-stone-200 text-stone-600 hover:bg-stone-100"
      }`}
    >
      <Sparkles className="w-3.5 h-3.5" />
      {cfg.name} plan
      {plan === "free" && <span className="text-indigo-600 font-semibold">· Upgrade</span>}
    </button>
  );
}

function UpgradeLockBar({ icon: Icon = Lock, title, subtitle, onUpgrade }) {
  return (
    <div className="flex items-center justify-between gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-amber-600" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-medium text-amber-900 truncate">{title}</p>
          {subtitle && <p className="text-[12px] text-amber-700/80 truncate">{subtitle}</p>}
        </div>
      </div>
      <button
        onClick={onUpgrade}
        className="shrink-0 text-[12.5px] font-medium bg-amber-600 hover:bg-amber-700 text-white rounded-lg px-3 py-1.5 whitespace-nowrap"
      >
        Upgrade to Pro
      </button>
    </div>
  );
}

function useMountedFade() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const raf = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(raf);
  }, []);
  return mounted;
}

/* =====================================================================
   GLOBAL DOC SEARCH
===================================================================== */

function DocSearch({ files, onSelect }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef(null);
  const inputRef = useRef(null);

  const results = q.trim()
    ? files
        .filter(
          (f) =>
            f.name.toLowerCase().includes(q.trim().toLowerCase()) ||
            (f.description || "").toLowerCase().includes(q.trim().toLowerCase())
        )
        .slice(0, 6)
    : [];

  useEffect(() => setHighlight(0), [q]);

  useEffect(() => {
    const onKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    const onClickOutside = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const pick = (file) => {
    if (!file) return;
    onSelect(file);
    setQ("");
    setOpen(false);
  };

  const onKeyDown = (e) => {
    if (e.key === "Escape") return setOpen(false);
    if (!results.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      pick(results[highlight]);
    }
  };

  return (
    <div ref={wrapRef} className="relative w-full max-w-md">
      <div className="flex items-center gap-2 bg-stone-100 rounded-lg px-3 py-1.5 border border-transparent focus-within:bg-white focus-within:border-stone-200 focus-within:ring-2 focus-within:ring-indigo-400/30 transition-colors">
        <Search className="w-3.5 h-3.5 text-stone-400 shrink-0" />
        <input
          ref={inputRef}
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search documents, then ask about one…"
          className="bg-transparent text-[13px] outline-none w-full placeholder:text-stone-400"
        />
        <kbd className="hidden sm:inline-flex shrink-0 items-center text-[10px] font-medium text-stone-400 bg-white border border-stone-200 rounded px-1.5 py-0.5">
          ⌘K
        </kbd>
      </div>

      {open && q.trim() && (
        <div className="absolute top-full left-0 right-0 mt-1.5 bg-white border border-stone-200 rounded-xl shadow-lg overflow-hidden z-30">
          {results.length === 0 ? (
            <div className="px-3 py-4 text-[12.5px] text-stone-400 text-center">No documents match "{q}"</div>
          ) : (
            results.map((f, i) => {
              const Icon = fileIcon(f.type);
              return (
                <button
                  key={f.id}
                  onMouseEnter={() => setHighlight(i)}
                  onClick={() => pick(f)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition-colors ${
                    i === highlight ? "bg-indigo-50" : "hover:bg-stone-50"
                  }`}
                >
                  <div className="w-6 h-6 rounded-md bg-stone-100 flex items-center justify-center shrink-0">
                    <Icon className="w-3.5 h-3.5 text-stone-500" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[12.5px] font-medium text-stone-800 truncate">{f.name}</p>
                    <p className="text-[11.5px] text-stone-400 truncate">
                      {f.description || f.collectionId || "Document"}
                    </p>
                  </div>
                  <span className={`text-[10.5px] font-medium shrink-0 ${i === highlight ? "text-indigo-600" : "text-stone-300"}`}>
                    Ask about this →
                  </span>
                </button>
              );
            })
          )}
          <div className="px-3 py-2 border-t border-stone-100 text-[11px] text-stone-400 bg-stone-50">
            Opens a new conversation scoped to just this document
          </div>
        </div>
      )}
    </div>
  );
}

/* =====================================================================
   TOP BAR
===================================================================== */

function TopBar({ route, onRouteChange, plan, onOpenUsage, onLogout, files, onTagDoc }) {
  const btnRefs = useRef({});
  const [indicator, setIndicator] = useState(null);

  useEffect(() => {
    const el = btnRefs.current[route];
    if (el) setIndicator({ left: el.offsetLeft, width: el.offsetWidth });
  }, [route]);

  return (
    <div className="h-12 shrink-0 border-b border-stone-200 flex items-center gap-4 px-3 bg-white/90 backdrop-blur-sm sticky top-0 z-20">
      <div className="relative flex items-center gap-1 shrink-0">
        {indicator && (
          <div
            className="absolute top-0 bottom-0 bg-stone-100 rounded-lg border border-stone-200 transition-all duration-200 ease-out"
            style={{ left: indicator.left, width: indicator.width }}
          />
        )}
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = route === item.id;
          return (
            <button
              key={item.id}
              ref={(el) => (btnRefs.current[item.id] = el)}
              onClick={() => onRouteChange(item.id)}
              className={`relative z-10 flex items-center gap-1.5 text-[12.5px] font-medium px-3 py-1.5 rounded-lg transition-colors ${
                active ? "text-stone-900" : "text-stone-500 hover:text-stone-700"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 flex justify-center min-w-0">
        <DocSearch files={files} onSelect={onTagDoc} />
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <PlanBadge plan={plan} onClick={onOpenUsage} />
        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 text-[12.5px] font-medium px-3 py-1.5 rounded-lg text-stone-500 hover:text-stone-700 hover:bg-stone-100 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign out
        </button>
      </div>
    </div>
  );
}

/* =====================================================================
   DASHBOARD — main shell
===================================================================== */

export default function Dashboard({ onLogout, initialPlan = "free" }) {
  const [route, setRoute] = useState("inbox");
  const [plan, setPlan] = useState(initialPlan);
  const [sourcesView, setSourcesView] = useState("sources");
  const [files, setFiles] = useState([]);
  const [pendingDocTag, setPendingDocTag] = useState(null);
  const [usageData, setUsageData] = useState(null);
  const mounted = useMountedFade();

  useEffect(() => {
    listDocuments()
      .then((docs) => {
        setFiles(docs.map(mapDocumentToFrontend));
      })
      .catch(() => {});
    getUsage().then(setUsageData).catch(() => {});
  }, []);

  const refreshFiles = useCallback(() => {
    listDocuments()
      .then((docs) => setFiles(docs.map(mapDocumentToFrontend)))
      .catch(() => {});
  }, []);

  const goToRoute = (id) => {
    if (id === "sources") setSourcesView("sources");
    setRoute(id);
  };
  const upgrade = () => setPlan("pro");
  const downgrade = () => setPlan("free");

  const tagDocInChat = (file) => {
    setPendingDocTag({ ...file, taggedAt: Date.now() });
    setRoute("inbox");
  };

  return (
    <div
      className={`h-screen w-full flex flex-col bg-white text-stone-900 font-[system-ui] transition-opacity duration-300 ${
        mounted ? "opacity-100" : "opacity-0"
      }`}
    >
      <TopBar
        route={route}
        onRouteChange={goToRoute}
        plan={plan}
        onOpenUsage={() => {
          setSourcesView("usage");
          setRoute("sources");
        }}
        onLogout={onLogout}
        files={files}
        onTagDoc={tagDocInChat}
      />

      <div className={`flex-1 min-h-0 ${route === "inbox" ? "" : "hidden"}`}>
        <ChatInboxDashboard
          onOpenSources={() => goToRoute("sources")}
          plan={plan}
          onUpgrade={upgrade}
          pendingDocTag={pendingDocTag}
          onConsumePendingDocTag={() => setPendingDocTag(null)}
          files={files}
          usageData={usageData}
          refreshFiles={refreshFiles}
        />
      </div>
      <div className={`flex-1 min-h-0 ${route === "sources" ? "" : "hidden"}`}>
        <RagFileManager
          onOpenInbox={() => setRoute("inbox")}
          plan={plan}
          onUpgrade={upgrade}
          onDowngrade={downgrade}
          view={sourcesView}
          setView={setSourcesView}
          files={files}
          setFiles={setFiles}
          onTagDoc={tagDocInChat}
          usageData={usageData}
          setUsageData={setUsageData}
        />
      </div>
    </div>
  );
}

/* =====================================================================
   AUTH — enterprise login / signup
===================================================================== */

function BrandMark({ tone = "dark" }) {
  const isDark = tone === "dark";
  return (
    <div className="flex items-center gap-2.5">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isDark ? "bg-blue-500" : "bg-slate-900"}`}>
        <Database className="w-4 h-4 text-white" />
      </div>
      <span className={`text-[15px] font-semibold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>DocSense</span>
    </div>
  );
}

const TRUST_POINTS = [
  { icon: Lock, title: "Role-based access", body: "Every collection and document inherits your org's permission model." },
  { icon: Database, title: "Source-grounded answers", body: "Every response cites the exact document and chunk it came from." },
  { icon: CheckCircle2, title: "Audit-ready", body: "Full trail of what was ingested, queried, and by whom." },
];

function AuthBrandPanel() {
  return (
    <div className="hidden lg:flex lg:w-[440px] shrink-0 flex-col justify-between bg-slate-900 px-10 py-10">
      <BrandMark tone="dark" />
      <div>
        <h2 className="text-[24px] font-semibold text-white leading-snug max-w-[320px]">
          Enterprise search, grounded in your own documents.
        </h2>
        <p className="text-[13.5px] text-slate-400 mt-3 max-w-[320px] leading-relaxed">
          DocSense indexes your organization's files into governed collections and answers only from what's been
          approved for retrieval.
        </p>
        <div className="mt-9 space-y-5">
          {TRUST_POINTS.map((p) => {
            const Icon = p.icon;
            return (
              <div key={p.title} className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-md bg-white/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Icon className="w-3.5 h-3.5 text-blue-400" />
                </div>
                <div>
                  <p className="text-[13px] font-medium text-white">{p.title}</p>
                  <p className="text-[12.5px] text-slate-400 mt-0.5 leading-relaxed">{p.body}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <p className="text-[11.5px] text-slate-500">SOC 2 Type II · Data encrypted at rest and in transit</p>
    </div>
  );
}

function AuthField({ icon: Icon, type = "text", onEnter, ...props }) {
  const [show, setShow] = useState(false);
  const isPassword = type === "password";
  return (
    <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-400">
      <Icon className="w-4 h-4 text-slate-400 shrink-0" />
      <input
        type={isPassword && show ? "text" : type}
        className="bg-transparent text-[13.5px] outline-none w-full placeholder:text-slate-400"
        onKeyDown={(e) => {
          if (e.key === "Enter" && onEnter) onEnter();
        }}
        {...props}
      />
      {isPassword && (
        <button type="button" onClick={() => setShow((v) => !v)} className="text-slate-400 hover:text-slate-600 shrink-0">
          {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      )}
    </div>
  );
}

function AuthShell({ children }) {
  const mounted = useMountedFade();
  return (
    <div className={`h-screen w-full flex bg-white font-[system-ui] transition-opacity duration-300 ${mounted ? "opacity-100" : "opacity-0"}`}>
      <AuthBrandPanel />
      <div className="flex-1 flex items-center justify-center px-6">
        <div
          className={`w-full max-w-[360px] transition-all duration-300 ease-out ${
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
          }`}
        >
          <div className="mb-8 flex lg:hidden">
            <BrandMark tone="light" />
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

function Login({ onAuthed, onGoToSignup }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = () => {
    if (loading) return;
    if (!email.trim() || !email.includes("@")) return setError("Enter a valid work email.");
    if (password.length < 6) return setError("Password must be at least 6 characters.");
    setError("");
    setLoading(true);
    setTimeout(() => onAuthed(), 650);
  };

  return (
    <AuthShell>
      <h1 className="text-[19px] font-semibold text-slate-900">Sign in to your workspace</h1>
      <p className="text-[13px] text-slate-500 mt-1 mb-7">Use your work email to continue.</p>
      <div className="space-y-3">
        <AuthField icon={Mail} type="email" placeholder="Work email" value={email} onChange={(e) => { setEmail(e.target.value); setError(""); }} />
        <AuthField icon={Lock} type="password" placeholder="Password" value={password} onChange={(e) => { setPassword(e.target.value); setError(""); }} onEnter={submit} />
        {error && (
          <p className="flex items-center gap-1.5 text-[12px] text-rose-600">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </p>
        )}
        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center gap-1.5 text-[12.5px] text-slate-500">
            <input type="checkbox" className="w-3.5 h-3.5 rounded border-slate-300 text-blue-600 focus:ring-blue-400 cursor-pointer" />
            Stay signed in
          </label>
          <button type="button" className="text-[12.5px] font-medium text-blue-600 hover:text-blue-700">Forgot password?</button>
        </div>
        <button onClick={submit} disabled={loading} className="w-full flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-70 text-white text-[13.5px] font-medium rounded-lg py-2.5 mt-2 transition-colors">
          {loading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Signing in…</> : <><span>Sign in</span><ArrowRight className="w-3.5 h-3.5" /></>}
        </button>
        <button type="button" className="w-full flex items-center justify-center gap-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13.5px] font-medium rounded-lg py-2.5 transition-colors">
          Continue with SSO
        </button>
      </div>
      <p className="text-[13px] text-slate-500 text-center mt-6">
        Need a workspace?{" "}
        <button onClick={onGoToSignup} className="font-medium text-blue-600 hover:text-blue-700">Create one</button>
      </p>
    </AuthShell>
  );
}

function PlanOption({ id, selected, onSelect }) {
  const cfg = PLANS[id];
  return (
    <button type="button" onClick={() => onSelect(id)} className={`flex-1 text-left rounded-lg border px-3 py-2.5 transition-colors ${selected ? "border-blue-500 bg-blue-50/60 ring-1 ring-blue-500/30" : "border-slate-200 hover:bg-slate-50"}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-[13px] font-semibold text-slate-900">{cfg.name}</span>
        {selected && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />}
      </div>
      <p className="text-[12px] text-slate-500 mt-0.5">
        {cfg.price} <span className="text-slate-400">{cfg.priceSub}</span>
      </p>
    </button>
  );
}

function Signup({ onAuthed, onGoToLogin }) {
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [selectedPlan, setSelectedPlan] = useState("free");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = () => {
    if (loading) return;
    if (!name.trim() || !company.trim()) return setError("Fill in your name and company to continue.");
    if (!email.trim() || !email.includes("@")) return setError("Enter a valid work email.");
    if (password.length < 6) return setError("Password must be at least 6 characters.");
    setError("");
    setLoading(true);
    setTimeout(() => onAuthed(selectedPlan), 650);
  };

  const clear = (setter) => (e) => {
    setter(e.target.value);
    setError("");
  };

  return (
    <AuthShell>
      <h1 className="text-[19px] font-semibold text-slate-900">Set up your workspace</h1>
      <p className="text-[13px] text-slate-500 mt-1 mb-6">Create an admin account for your organization.</p>
      <div className="space-y-3">
        <AuthField icon={User} type="text" placeholder="Full name" value={name} onChange={clear(setName)} />
        <AuthField icon={Database} type="text" placeholder="Company name" value={company} onChange={clear(setCompany)} />
        <AuthField icon={Mail} type="email" placeholder="Work email" value={email} onChange={clear(setEmail)} />
        <AuthField icon={Lock} type="password" placeholder="Password" value={password} onChange={clear(setPassword)} onEnter={submit} />
        <div>
          <p className="text-[12px] font-medium text-slate-500 mb-1.5 mt-1">Starting plan</p>
          <div className="flex gap-2">
            <PlanOption id="free" selected={selectedPlan === "free"} onSelect={setSelectedPlan} />
            <PlanOption id="pro" selected={selectedPlan === "pro"} onSelect={setSelectedPlan} />
          </div>
          <p className="text-[11.5px] text-slate-400 mt-1.5">You can change plans anytime from Usage settings.</p>
        </div>
        {error && (
          <p className="flex items-center gap-1.5 text-[12px] text-rose-600">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </p>
        )}
        <p className="text-[12px] text-slate-400 pt-1">By continuing, you agree to the Terms and Data Processing Agreement.</p>
        <button onClick={submit} disabled={loading} className="w-full flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-70 text-white text-[13.5px] font-medium rounded-lg py-2.5 mt-2 transition-colors">
          {loading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Creating workspace…</> : <><span>Create workspace</span><ArrowRight className="w-3.5 h-3.5" /></>}
        </button>
      </div>
      <p className="text-[13px] text-slate-500 text-center mt-6">
        Already have a workspace?{" "}
        <button onClick={onGoToLogin} className="font-medium text-blue-600 hover:text-blue-700">Sign in</button>
      </p>
    </AuthShell>
  );
}

/* =====================================================================
   ROOT ROUTER
 ===================================================================== */

export function RootApp() {
  const [screen, setScreen] = useState("login");
  const [initialPlan, setInitialPlan] = useState("free");

  if (screen === "signup") {
    return (
      <Signup
        onAuthed={(plan) => {
          setInitialPlan(plan || "free");
          setScreen("dashboard");
        }}
        onGoToLogin={() => setScreen("login")}
      />
    );
  }
  if (screen === "dashboard") {
    return <Dashboard onLogout={() => setScreen("login")} initialPlan={initialPlan} />;
  }
  return (
    <Login
      onAuthed={() => {
        setInitialPlan("free");
        setScreen("dashboard");
      }}
      onGoToSignup={() => setScreen("signup")}
    />
  );
}

/* =====================================================================
   DOCUMENT HELPERS
===================================================================== */

const ICONS = { pdf: FileText, docx: FileText, csv: FileSpreadsheet, json: FileJson, url: LinkIcon, default: File };
const fileIcon = (t) => ICONS[t] || ICONS.default;
const formatBytes = (b) =>
  b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`;

const STATUS_CONFIG = {
  completed: { label: "Indexed", icon: CheckCircle2, dot: "bg-emerald-500", text: "text-emerald-700" },
  processing: { label: "Indexing", icon: Loader2, dot: "bg-amber-500", text: "text-amber-700", spin: true },
  uploaded: { label: "Indexing", icon: Loader2, dot: "bg-amber-500", text: "text-amber-700", spin: true },
  failed: { label: "Failed", icon: AlertCircle, dot: "bg-rose-500", text: "text-rose-700" },
  queued: { label: "Queued", icon: RotateCw, dot: "bg-stone-400", text: "text-stone-500" },
};

function mapDocumentToFrontend(doc) {
  const ext = doc.original_filename.split(".").pop().toLowerCase();
  return {
    id: doc.id,
    name: doc.original_filename,
    description: "",
    type: ext,
    size: doc.file_size,
    chunks: doc.chunk_count ?? null,
    collectionId: "default",
    status: doc.status === "completed" ? "indexed" : doc.status,
    updated: formatRelativeTime(doc.updated_at),
    created_at: doc.created_at,
  };
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function formatConversationDate(dateStr) {
  if (!dateStr) return null;
  const d = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now - d) / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return d.toLocaleDateString("en-US", { weekday: "short" });
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/* =====================================================================
   PAGE 1 — QUERY CONSOLE (RAG chat)
===================================================================== */

const STATUS = {
  amber: { dot: "bg-amber-400" },
  rose: { dot: "bg-rose-400" },
  emerald: { dot: "bg-emerald-400" },
  sky: { dot: "bg-sky-400" },
};

const PIPELINE_STAGES = [
  { id: "query", label: "Query analysis", icon: Search },
  { id: "vector", label: "Vector search", icon: Type },
  { id: "lexical", label: "Lexical search", icon: Type },
  { id: "fusion", label: "RRF fusion", icon: GitMerge },
  { id: "rerank", label: "Reranking", icon: Sparkles },
  { id: "grade", label: "Grading evidence", icon: ShieldCheck },
];

const CONFIDENCE_CONFIG = {
  grounded: { label: "Grounded", icon: ShieldCheck, className: "text-emerald-700 bg-emerald-50" },
  partial: { label: "Partially grounded", icon: AlertTriangle, className: "text-amber-700 bg-amber-50" },
  unsupported: { label: "Low confidence", icon: AlertCircle, className: "text-rose-700 bg-rose-50" },
};

function getConfidenceLevel(score) {
  if (score == null) return "unsupported";
  if (score >= 0.75) return "grounded";
  if (score >= 0.45) return "partial";
  return "unsupported";
}

function ConfidenceBadge({ confidence }) {
  const cfg = CONFIDENCE_CONFIG[confidence] || CONFIDENCE_CONFIG.grounded;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11.5px] font-medium px-2 py-1 rounded-full shrink-0 ${cfg.className}`}>
      <Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  );
}

function AnswerText({ text, onCiteClick, activeCite }) {
  if (!text) return null;
  const parts = text.split(/(\[\d+\])/g);
  return (
    <div className="markdown-body text-[14px] text-stone-700 leading-relaxed">
      {parts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (!m) {
          return <ReactMarkdown key={i}>{part}</ReactMarkdown>;
        }
        const n = m[1];
        return (
          <button
            key={i}
            onClick={() => onCiteClick(n)}
            className={`inline-flex items-center justify-center align-super text-[10px] font-semibold w-4 h-4 rounded mx-0.5 -translate-y-0.5 transition-colors ${
              activeCite === n ? "bg-indigo-600 text-white" : "bg-indigo-50 text-indigo-600 hover:bg-indigo-100"
            }`}
          >
            {n}
          </button>
        );
      })}
    </div>
  );
}

function SourceCard({ source, active, onSelect }) {
  const ext = source.file.split(".").pop().toLowerCase();
  const Icon = fileIcon(ext);
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left flex items-start gap-2.5 px-3 py-2.5 rounded-lg border transition-colors ${
        active ? "border-indigo-300 bg-indigo-50/60" : "border-stone-100 hover:bg-stone-50"
      }`}
    >
      <span className="w-5 h-5 rounded-md bg-stone-100 flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-semibold text-stone-500">
        {source.n}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <Icon className="w-3 h-3 text-stone-400 shrink-0" />
          <span className="text-[12.5px] font-medium text-stone-800 truncate">{source.file}</span>
          <span className="text-[11px] text-stone-400 shrink-0">· {source.loc}</span>
        </div>
        <p className="text-[12px] text-stone-500 mt-1 leading-snug line-clamp-2">
          <Quote className="w-2.5 h-2.5 inline mr-1 text-stone-300" />
          {source.snippet}
        </p>
        {source.score != null && (
          <div className="flex items-center gap-1.5 mt-1.5">
            <div className="flex-1 h-1 bg-stone-100 rounded-full overflow-hidden max-w-[80px]">
              <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${Math.round(source.score * 100)}%` }} />
            </div>
            <span className="text-[10.5px] text-stone-400 tabular-nums">{Math.round(source.score * 100)}% match</span>
          </div>
        )}
      </div>
    </button>
  );
}

function UserTurn({ text }) {
  return (
    <div className="py-3">
      <p className="text-[15px] font-medium text-stone-900 leading-snug">{text}</p>
    </div>
  );
}

function AssistantTurn({ turn, documents, onRegenerate, isLast, regenerateLocked }) {
  const [activeCite, setActiveCite] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const sources = (turn.sources || []).map((s, i) => {
    const doc = documents.find((d) => d.id === s.document_id);
    return {
      n: i + 1,
      file: doc ? doc.name : `Document #${s.document_id}`,
      loc: `p. ${s.page_number}`,
      snippet: s.content,
      score: s.score,
      document_id: s.document_id,
    };
  });

  const confidenceLevel = getConfidenceLevel(turn.confidence);

  return (
    <div className="py-4">
      {turn.abstained ? (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-3">
          <div className="flex items-center gap-2 text-[13px] font-medium text-amber-800 mb-1">
            <AlertTriangle className="w-4 h-4" />
            Unable to answer
          </div>
          <p className="text-[12.5px] text-amber-700">
            {turn.abstention_reason || "The available documents don't contain enough information to answer this question."}
          </p>
          {turn.abstention_suggestion && (
            <p className="text-[12px] text-amber-600 mt-1">Suggestion: {turn.abstention_suggestion}</p>
          )}
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <ConfidenceBadge confidence={confidenceLevel} />
          </div>
          <AnswerText text={turn.answer} onCiteClick={setActiveCite} activeCite={activeCite} />

          {sources.length > 0 && (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {sources.map((s) => (
                <SourceCard key={s.n} source={s} active={activeCite === String(s.n)} onSelect={() => setActiveCite(String(s.n))} />
              ))}
            </div>
          )}
        </>
      )}

      <div className="flex items-center gap-2 mt-3">
        <button
          onClick={() => setFeedback(feedback === "up" ? null : "up")}
          className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
            feedback === "up" ? "bg-emerald-50 text-emerald-600" : "hover:bg-stone-100 text-stone-400"
          }`}
        >
          <ThumbsUp className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setFeedback(feedback === "down" ? null : "down")}
          className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
            feedback === "down" ? "bg-rose-50 text-rose-600" : "hover:bg-stone-100 text-stone-400"
          }`}
        >
          <ThumbsDown className="w-3.5 h-3.5" />
        </button>
        {isLast && !regenerateLocked && (
          <button onClick={onRegenerate} className="flex items-center gap-1.5 text-[12px] text-stone-400 hover:text-stone-600 ml-1">
            <RotateCw className="w-3.5 h-3.5" />
            Regenerate
          </button>
        )}
      </div>
    </div>
  );
}

function PipelineRunning({ stageIndex }) {
  return (
    <div className="py-4">
      <div className="flex flex-wrap items-center gap-1">
        {PIPELINE_STAGES.map((s, i) => {
          const Icon = s.icon;
          const done = i < stageIndex;
          const active = i === stageIndex;
          return (
            <span key={s.id} className="flex items-center">
              <span
                className={`inline-flex items-center gap-1 text-[11px] font-medium rounded-full px-2 py-1 border transition-colors ${
                  done ? "bg-emerald-50 border-emerald-200 text-emerald-700" : active ? "bg-indigo-50 border-indigo-200 text-indigo-700" : "bg-white border-stone-200 text-stone-400"
                }`}
              >
                {active ? <Loader2 className="w-3 h-3 animate-spin" /> : done ? <CheckCircle2 className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
                {s.label}
              </span>
              {i < PIPELINE_STAGES.length - 1 && <ArrowRight className="w-3 h-3 text-stone-300 mx-1" />}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function ChatRow({ chat, isActive, onClick }) {
  const dateStr = formatConversationDate(chat.updated_at || chat.created_at);
  const toneKey = chat.abstained ? "sky" : chat.confidence != null ? (chat.confidence >= 0.75 ? "emerald" : chat.confidence >= 0.45 ? "amber" : "rose") : "sky";
  const tone = STATUS[toneKey];

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-3 border-b border-stone-100 transition-colors ${
        isActive ? "bg-indigo-50/70" : "hover:bg-stone-50"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13.5px] font-medium text-stone-800 leading-snug line-clamp-2 flex items-center gap-1.5">
          {chat.document_ids && chat.document_ids.length > 0 && <FileText className="w-3 h-3 text-indigo-400 shrink-0" />}
          <span className="line-clamp-2">{chat.title}</span>
        </p>
        {isActive && (
          <div className="flex items-center gap-2 shrink-0 pt-0.5 text-stone-400">
            <Star className="w-3.5 h-3.5" />
            <MoreVertical className="w-3.5 h-3.5" />
          </div>
        )}
      </div>
      <div className="flex items-center gap-1.5 mt-1.5">
        <span className={`w-2 h-2 rounded-full ${tone.dot}`} />
        <span className="text-[12px] text-stone-500">
          {chat.document_ids && chat.document_ids.length > 0 ? `${chat.document_ids.length} source${chat.document_ids.length === 1 ? "" : "s"}` : "All sources"}
        </span>
        {dateStr && <span className="text-[12px] text-stone-400 ml-auto">{dateStr}</span>}
      </div>
    </button>
  );
}

function DocumentPicker({ files, selectedIds, onToggle, onClear, onConfirm, onUpload, onUploadComplete, pickerRef }) {
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await onUpload(file);
      onUploadComplete?.();
    } catch {
      // Silently fail
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div ref={pickerRef} className="absolute bottom-full left-0 mb-2 w-80 bg-white border border-stone-200 rounded-xl shadow-lg overflow-hidden z-50">
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-stone-100">
        <span className="text-[13px] font-semibold text-stone-800">Select documents</span>
        <div className="flex items-center gap-1">
          <button onClick={onClear} className="text-[11.5px] text-stone-400 hover:text-stone-600 px-1.5 py-0.5 rounded hover:bg-stone-50">Clear</button>
          <button onClick={() => onConfirm()} className="text-[11.5px] text-indigo-600 hover:text-indigo-700 font-medium px-1.5 py-0.5 rounded hover:bg-indigo-50">Done</button>
        </div>
      </div>
      <div className="max-h-56 overflow-y-auto">
        {files.length === 0 ? (
          <div className="px-3 py-6 text-center">
            <FileText className="w-8 h-8 text-stone-300 mx-auto mb-2" />
            <p className="text-[12.5px] text-stone-500 mb-3">No documents uploaded yet.</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="inline-flex items-center gap-1.5 text-[12.5px] font-medium text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
            >
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UploadCloud className="w-3.5 h-3.5" />}
              {uploading ? "Uploading…" : "Upload a document"}
            </button>
            <input ref={fileInputRef} type="file" accept=".pdf,.csv,.xlsx,.xls,.pptx,.docx" className="hidden" onChange={handleUpload} />
          </div>
        ) : (
          files.map((f) => {
            const selected = selectedIds.includes(f.id);
            return (
              <button
                key={f.id}
                onClick={() => onToggle(f.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors ${selected ? "bg-indigo-50/70" : "hover:bg-stone-50"}`}
              >
                <span className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${selected ? "bg-indigo-600 border-indigo-600" : "border-stone-300"}`}>
                  {selected && <CheckCircle2 className="w-3 h-3 text-white" />}
                </span>
                <FileText className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                <span className="text-[12.5px] text-stone-700 truncate flex-1">{f.name}</span>
                <span className="text-[11px] text-stone-400 shrink-0">{f.status === "completed" ? "Indexed" : f.status}</span>
              </button>
            );
          })
        )}
      </div>
      {files.length > 0 && (
        <div className="px-3 py-2 border-t border-stone-100 flex items-center justify-between">
          <span className="text-[11.5px] text-stone-400">{selectedIds.length} of {files.length} selected</span>
          <div className="flex items-center gap-2">
            <input ref={fileInputRef} type="file" accept=".pdf,.csv,.xlsx,.xls,.pptx,.docx" className="hidden" onChange={handleUpload} />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="text-[11.5px] text-stone-500 hover:text-stone-700 flex items-center gap-1 disabled:opacity-50"
            >
              {uploading ? <Loader2 className="w-3 h-3 animate-spin" /> : <UploadCloud className="w-3 h-3" />}
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ChatInboxDashboard({ onOpenSources, plan, onUpgrade, pendingDocTag, onConsumePendingDocTag, files, usageData, refreshFiles }) {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [turnsById, setTurnsById] = useState({});
  const [input, setInput] = useState("");
  const [pipeline, setPipeline] = useState(null);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [search, setSearch] = useState("");
  const [scopedDocIds, setScopedDocIds] = useState([]);
  const [showDocPicker, setShowDocPicker] = useState(false);
  const scrollRef = useRef(null);
  const docPickerRef = useRef(null);
  const mounted = useMountedFade();

  const activeChat = conversations.find((c) => c.id === activeId);
  const turns = turnsById[activeId] || [];
  const filtered = conversations.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()));

  useEffect(() => {
    setLoadingConversations(true);
    listConversations(0, 50)
      .then((res) => {
        setConversations(res.conversations || []);
        if (res.conversations.length > 0) {
          setActiveId(res.conversations[0].id);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingConversations(false));
  }, []);

  useEffect(() => {
    if (!activeId) return;
    if (turnsById[activeId]) return;
    getConversation(activeId)
      .then((detail) => {
        const mapped = (detail.messages || []).flatMap((msg) => {
          if (msg.role === "user") return [{ role: "user", text: msg.content }];
          return [{
            role: "assistant",
            answer: msg.content,
            confidence: msg.confidence,
            abstained: msg.abstained,
            abstention_reason: msg.abstention_reason,
            sources: [],
            attempts: [{ query: "", sufficient: !msg.abstained }],
          }];
        });
        setTurnsById((prev) => ({ ...prev, [activeId]: mapped }));
      })
      .catch(() => {});
  }, [activeId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => setEditingTitle(false), [activeId]);

  useEffect(() => {
    if (!showDocPicker) return;
    const handleClick = (e) => {
      if (docPickerRef.current && !docPickerRef.current.contains(e.target)) {
        setShowDocPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showDocPicker]);

  const openChat = (id) => {
    setActiveId(id);
    setSearch("");
  };

  const addChat = async () => {
    try {
      const conv = await createConversation("New conversation");
      setConversations((prev) => [conv, ...prev]);
      setTurnsById((prev) => ({ ...prev, [conv.id]: [] }));
      openChat(conv.id);
    } catch {
      // Silently fail
    }
  };

  useEffect(() => {
    if (!pendingDocTag) return;
    (async () => {
      try {
        const conv = await createConversation(`About ${pendingDocTag.name}`, [pendingDocTag.id]);
        setConversations((prev) => [conv, ...prev]);
        setTurnsById((prev) => ({ ...prev, [conv.id]: [] }));
        openChat(conv.id);
        onConsumePendingDocTag?.();
      } catch {
        // Silently fail
      }
    })();
  }, [pendingDocTag]); // eslint-disable-line react-hooks/exhaustive-deps

  const clearScope = async (id) => {
    try {
      await updateConversationTitle(id, activeChat.title);
      setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, document_ids: null } : c)));
    } catch {
      // Silently fail
    }
  };

  const startEditTitle = () => {
    setTitleDraft(activeChat?.title || "");
    setEditingTitle(true);
  };

  const commitTitle = async () => {
    setEditingTitle(false);
    const next = titleDraft.trim();
    if (!next || !activeId) return;
    try {
      await updateConversationTitle(activeId, next);
      setConversations((prev) => prev.map((c) => (c.id === activeId ? { ...c, title: next } : c)));
    } catch {
      // Silently fail
    }
  };

  const queryLimit = PLANS[plan].queryLimit;
  const queriesUsed = usageData?.queries_this_month ?? Object.values(turnsById).reduce((sum, arr) => sum + arr.filter((t) => t.role === "user").length, 0);
  const queryLimitReached = plan === "free" && queriesUsed >= queryLimit;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns.length, pipeline]);

  const submit = async () => {
    const text = input.trim();
    if (!text || pipeline || queryLimitReached || !activeId) return;
    setInput("");

    const userTurn = { role: "user", text };
    setTurnsById((prev) => ({ ...prev, [activeId]: [...(prev[activeId] || []), userTurn] }));

    let stage = 0;
    setPipeline({ stageIndex: 0 });
    const stageTimer = setInterval(() => {
      stage += 1;
      if (stage < PIPELINE_STAGES.length) {
        setPipeline({ stageIndex: stage });
      }
    }, 300);

    try {
      const docIds = scopedDocIds.length > 0 ? scopedDocIds : null;
      const result = await sendChat({
        query: text,
        conversation_id: activeId,
        document_ids: docIds,
      });

      clearInterval(stageTimer);
      setPipeline(null);

      const assistantTurn = {
        role: "assistant",
        answer: result.answer,
        sources: result.sources || [],
        confidence: result.confidence,
        abstained: result.abstained,
        abstention_reason: result.abstention_reason,
        abstention_suggestion: result.abstention_suggestion,
        query: text,
        attempts: [{ query: text, sufficient: !result.abstained }],
      };

      setTurnsById((prev) => ({ ...prev, [activeId]: [...(prev[activeId] || []), assistantTurn] }));

      setConversations((prev) => prev.map((c) => (c.id === activeId ? { ...c, updated_at: new Date().toISOString() } : c)));
    } catch (err) {
      clearInterval(stageTimer);
      setPipeline(null);
      const errorTurn = {
        role: "assistant",
        answer: "Sorry, something went wrong. Please try again.",
        sources: [],
        confidence: 0,
        abstained: true,
        abstention_reason: err?.message || "Request failed",
        query: text,
        attempts: [{ query: text, sufficient: false, reason: "Request failed" }],
      };
      setTurnsById((prev) => ({ ...prev, [activeId]: [...(prev[activeId] || []), errorTurn] }));
    }
  };

  const regenerate = async () => {
    if (pipeline || queryLimitReached || !activeId) return;
    const lastUser = [...turns].reverse().find((t) => t.role === "user");
    if (!lastUser) return;

    setTurnsById((prev) => ({ ...prev, [activeId]: prev[activeId].slice(0, -1) }));

    let stage = 0;
    setPipeline({ stageIndex: 0 });
    const stageTimer = setInterval(() => {
      stage += 1;
      if (stage < PIPELINE_STAGES.length) {
        setPipeline({ stageIndex: stage });
      }
    }, 300);

    try {
      const docIds = scopedDocIds.length > 0 ? scopedDocIds : null;
      const result = await sendChat({
        query: lastUser.text,
        conversation_id: activeId,
        document_ids: docIds,
      });

      clearInterval(stageTimer);
      setPipeline(null);

      const assistantTurn = {
        role: "assistant",
        answer: result.answer,
        sources: result.sources || [],
        confidence: result.confidence,
        abstained: result.abstained,
        abstention_reason: result.abstention_reason,
        query: lastUser.text,
        attempts: [{ query: lastUser.text, sufficient: !result.abstained }],
      };

      setTurnsById((prev) => ({ ...prev, [activeId]: [...prev[activeId], assistantTurn] }));
    } catch {
      clearInterval(stageTimer);
      setPipeline(null);
    }
  };

  return (
    <div className={`h-full w-full flex bg-white text-stone-900 transition-opacity duration-200 ${mounted ? "opacity-100" : "opacity-0"}`}>
      {/* Sidebar */}
      <aside className="w-[300px] shrink-0 border-r border-stone-200 flex flex-col">
        <div className="flex items-center justify-between px-4 pt-4 pb-3">
          <h1 className="text-[15px] font-semibold tracking-tight">DocSense</h1>
          <button
            onClick={addChat}
            title="New chat"
            className="w-8 h-8 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="px-4 pb-3">
          <div className="flex items-center gap-2 bg-stone-100 rounded-lg px-3 py-2">
            <Search className="w-4 h-4 text-stone-400 shrink-0" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Find a query"
              className="bg-transparent text-[13px] outline-none w-full placeholder:text-stone-400"
            />
            <SlidersHorizontal className="w-4 h-4 text-stone-400 shrink-0" />
          </div>
        </div>

        <div className="px-4 pb-2 text-[12px] font-medium text-stone-400">Chat</div>

        <div className="flex-1 overflow-y-auto">
          {loadingConversations ? (
            <div className="px-4 py-8 text-center text-[12.5px] text-stone-400">Loading conversations…</div>
          ) : filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-[12.5px] text-stone-400">No conversations yet</div>
          ) : (
            filtered.map((chat) => (
              <ChatRow key={chat.id} chat={chat} isActive={chat.id === activeId} onClick={() => openChat(chat.id)} />
            ))
          )}
        </div>

        {plan === "free" && (
          <div className="px-4 py-3 border-t border-stone-100">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-medium text-stone-400 uppercase tracking-wide">Monthly queries</span>
              <span className="text-[11px] text-stone-400 tabular-nums">
                {Math.min(queriesUsed, queryLimit)}/{queryLimit}
              </span>
            </div>
            <div className="w-full h-1.5 bg-stone-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${queryLimitReached ? "bg-rose-400" : "bg-indigo-400"}`}
                style={{ width: `${Math.min(100, (queriesUsed / queryLimit) * 100)}%` }}
              />
            </div>
          </div>
        )}
      </aside>

      {/* Main panel */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center justify-between px-8 pt-5 pb-4 border-b border-stone-100">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            {editingTitle ? (
              <input
                autoFocus
                value={titleDraft}
                onChange={(e) => setTitleDraft(e.target.value)}
                onBlur={commitTitle}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitTitle();
                  if (e.key === "Escape") setEditingTitle(false);
                }}
                className="text-[17px] font-semibold text-stone-900 bg-stone-50 border border-indigo-300 rounded-md px-2 py-0.5 outline-none min-w-0 flex-1"
              />
            ) : (
              <>
                <h2 className="text-[17px] font-semibold text-stone-900 truncate">{activeChat?.title || "Select a conversation"}</h2>
                {activeChat && (
                  <button onClick={startEditTitle} title="Rename chat" className="text-stone-400 hover:text-stone-600 shrink-0">
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                )}
              </>
            )}
          </div>
          <MoreVertical className="w-4 h-4 text-stone-400 shrink-0" />
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-8">
          {!activeId ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <div className="w-14 h-14 rounded-full bg-indigo-50 flex items-center justify-center mb-4">
                <MessageSquare className="w-6 h-6 text-indigo-400" />
              </div>
              <p className="text-[15px] font-medium text-stone-700">Start a new conversation</p>
              <p className="text-[13px] text-stone-400 mt-1">Ask questions about your indexed documents</p>
              <button onClick={addChat} className="mt-4 flex items-center gap-1.5 text-[13px] font-medium text-indigo-600 hover:text-indigo-700">
                <Plus className="w-4 h-4" />
                New chat
              </button>
            </div>
          ) : (
            <div className="divide-y divide-stone-100">
              {turns.map((t, i) =>
                t.role === "user" ? (
                  <UserTurn key={i} text={t.text} />
                ) : (
                  <AssistantTurn
                    key={i}
                    turn={t}
                    documents={files}
                    onRegenerate={regenerate}
                    isLast={i === turns.length - 1}
                    regenerateLocked={queryLimitReached}
                  />
                )
              )}
            </div>
          )}

          {pipeline && <PipelineRunning stageIndex={pipeline.stageIndex} />}
        </div>

        <div className="px-8 pb-6 pt-2 relative">
          {queryLimitReached ? (
            <UpgradeLockBar
              icon={MessageSquare}
              title={`You've used all ${queryLimit} free queries this month`}
              subtitle="Upgrade to Pro for unlimited queries across every collection."
              onUpgrade={onUpgrade}
            />
          ) : (
            <>
              {scopedDocIds.length > 0 && (
                <div className="flex items-center gap-1.5 mb-2 flex-wrap">
                  <span className="text-[11.5px] text-stone-400">Scoped to:</span>
                  {scopedDocIds.map((id) => {
                    const doc = files.find((f) => f.id === id);
                    if (!doc) return null;
                    return (
                      <span key={id} className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 text-[11.5px] font-medium px-2 py-0.5 rounded-full">
                        {doc.name}
                        <button onClick={() => setScopedDocIds((prev) => prev.filter((d) => d !== id))} className="hover:text-indigo-900">
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    );
                  })}
                  <button onClick={() => setScopedDocIds([])} className="text-[11px] text-stone-400 hover:text-stone-600 ml-1">Clear all</button>
                </div>
              )}
              <div className="flex items-center gap-2 bg-stone-100 rounded-xl px-4 py-3 relative">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && submit()}
                  placeholder={pipeline ? "Retrieving…" : "Ask a follow-up"}
                  disabled={!!pipeline || !activeId}
                  className="bg-transparent text-[13.5px] outline-none w-full placeholder:text-stone-400 disabled:cursor-not-allowed"
                />
                <button
                  onClick={() => setShowDocPicker((v) => !v)}
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-colors ${scopedDocIds.length > 0 ? "bg-indigo-100 text-indigo-600 hover:bg-indigo-200" : "hover:bg-stone-200 text-stone-500"}`}
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <button
                  onClick={submit}
                  disabled={!!pipeline || !input.trim() || !activeId}
                  className="w-8 h-8 rounded-full bg-stone-900 hover:bg-stone-800 disabled:opacity-40 flex items-center justify-center text-white shrink-0"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
                {showDocPicker && (
                  <DocumentPicker
                    pickerRef={docPickerRef}
                    files={files}
                    selectedIds={scopedDocIds}
                    onToggle={(id) => setScopedDocIds((prev) => prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id])}
                    onClear={() => setScopedDocIds([])}
                    onConfirm={() => setShowDocPicker(false)}
                    onUpload={uploadDocument}
                    onUploadComplete={refreshFiles}
                  />
                )}
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

/* =====================================================================
   PAGE 2 — RAG FILE MANAGER
===================================================================== */

function StatusIndicator({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.queued;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 text-[12.5px] font-medium ${cfg.text}`}>
      {status === "processing" || status === "uploaded" ? (
        <Icon className={`w-3 h-3 ${cfg.spin ? "animate-spin" : ""}`} />
      ) : (
        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      )}
      {cfg.label}
    </span>
  );
}

function FileRow({ file, selected, onToggleSelect, onRetry, onRequestDelete, onChat }) {
  const Icon = fileIcon(file.type);

  return (
    <div
      className={`flex items-center gap-3 pl-4 pr-3 py-1.5 border-b border-stone-100 group ${
        selected ? "bg-indigo-50/50" : "hover:bg-stone-50/80"
      }`}
    >
      <input
        type="checkbox"
        checked={selected}
        onChange={() => onToggleSelect(file.id)}
        className="w-3.5 h-3.5 rounded border-stone-300 text-indigo-600 focus:ring-indigo-400 cursor-pointer shrink-0"
      />

      <div className="w-6 h-6 rounded-md bg-stone-100 flex items-center justify-center shrink-0">
        <Icon className="w-3.5 h-3.5 text-stone-500" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-1.5 min-w-0">
          <span className="text-[13px] font-medium text-stone-800 truncate shrink-0 max-w-[45%]">{file.name}</span>
        </div>
        {file.status === "failed" && file.error && <p className="text-[11px] text-rose-500 truncate">{file.error}</p>}
        {(file.status === "processing" || file.status === "uploaded") && file.progress != null && (
          <div className="mt-0.5 h-[3px] w-28 bg-stone-100 rounded-full overflow-hidden">
            <div className="h-full bg-amber-400 rounded-full transition-all" style={{ width: `${file.progress || 0}%` }} />
          </div>
        )}
      </div>

      <div style={{ width: 100 }} className="shrink-0">
        <StatusIndicator status={file.status} />
      </div>
      <div style={{ width: 80 }} className="shrink-0 text-[12px] text-stone-500 tabular-nums text-right">
        {formatBytes(file.size)}
      </div>
      <div style={{ width: 90 }} className="shrink-0 text-[12px] text-stone-500 tabular-nums text-right">
        {file.chunks != null ? `${file.chunks} chunks` : "—"}
      </div>
      <div style={{ width: 64 }} className="shrink-0 text-[11.5px] text-stone-400 text-right whitespace-nowrap">
        {file.updated}
      </div>

      <div style={{ width: 138 }} className="shrink-0 flex items-center justify-end gap-1">
        {file.status === "indexed" || file.status === "completed" ? (
          <button
            onClick={() => onChat(file)}
            title={`Chat about ${file.name}`}
            className="flex items-center gap-1 text-[11.5px] font-medium text-indigo-600 hover:bg-indigo-50 rounded-md px-1.5 py-1 whitespace-nowrap"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Chat
          </button>
        ) : (
          <span style={{ width: 54 }} className="shrink-0" />
        )}
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          {file.status === "failed" && (
            <button onClick={() => onRetry(file.id)} title="Retry" className="w-6 h-6 rounded-md hover:bg-stone-200 flex items-center justify-center text-stone-500">
              <RotateCw className="w-3.5 h-3.5" />
            </button>
          )}
          <button onClick={() => onRequestDelete(file)} title="Remove" className="w-6 h-6 rounded-md hover:bg-rose-50 flex items-center justify-center text-stone-400 hover:text-rose-500">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

function DeleteConfirmModal({ target, onCancel, onConfirm }) {
  if (!target) return null;
  const isBulk = Array.isArray(target);
  const label = isBulk ? `${target.length} files` : `"${target.name}"`;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-5">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-full bg-rose-50 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div>
            <h3 className="text-[14.5px] font-semibold text-stone-900">Delete {label}?</h3>
            <p className="text-[13px] text-stone-500 mt-1">
              This removes the {isBulk ? "files" : "file"} and every chunk indexed from {isBulk ? "them" : "it"} from
              the assistant's knowledge base. This can't be undone.
            </p>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 mt-5">
          <button onClick={onCancel} className="text-[13px] font-medium px-3 py-1.5 rounded-lg text-stone-600 hover:bg-stone-100">
            Cancel
          </button>
          <button onClick={onConfirm} className="text-[13px] font-medium px-3 py-1.5 rounded-lg bg-rose-500 text-white hover:bg-rose-600">
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="border border-stone-100 rounded-xl px-4 py-3.5">
      <div className="flex items-center gap-2 text-stone-400 mb-2">
        <Icon className="w-3.5 h-3.5" />
        <span className="text-[12px] font-medium">{label}</span>
      </div>
      <p className="text-[20px] font-semibold text-stone-900 leading-none">{value}</p>
      {sub && <p className="text-[12px] text-stone-400 mt-1.5">{sub}</p>}
    </div>
  );
}

function UsageView({ files, plan, onUpgrade, onDowngrade, usageData }) {
  const storageLimitBytes = PLANS[plan].storageLimitBytes;
  const totalStorage = files.reduce((sum, f) => sum + (f.size || 0), 0);
  const totalChunks = usageData?.chunks_stored ?? files.reduce((sum, f) => sum + (f.chunks || 0), 0);
  const totalQueries = usageData?.queries_this_month ?? 0;
  const docsUploaded = usageData?.documents_uploaded ?? files.length;
  const storagePct = Math.min(100, (totalStorage / storageLimitBytes) * 100);

  const perCollection = [
    {
      id: "all",
      name: "All Sources",
      storage: totalStorage,
      chunks: totalChunks,
      queries: totalQueries,
      files: docsUploaded,
    },
  ];

  const mostQueried = [...files].sort((a, b) => (b.queries || 0) - (a.queries || 0)).slice(0, 5);

  return (
    <div className="px-8 py-6 overflow-y-auto flex-1">
      <div className="flex items-center justify-between mb-5 border border-stone-100 rounded-xl px-4 py-3">
        <div className="flex items-center gap-2 text-[13px]">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
          <span className="text-stone-600">
            Current plan: <span className="font-semibold text-stone-900">{PLANS[plan].name}</span>
          </span>
        </div>
        {plan === "free" ? (
          <button onClick={onUpgrade} className="text-[12.5px] font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-3 py-1.5">
            Upgrade to Pro
          </button>
        ) : (
          <button onClick={onDowngrade} className="text-[12.5px] font-medium text-stone-500 hover:text-stone-700 border border-stone-200 rounded-lg px-3 py-1.5">
            Switch to Free (test)
          </button>
        )}
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <SummaryCard icon={Database} label="Storage used" value={formatBytes(totalStorage)} sub={`${storagePct.toFixed(1)}% of ${formatBytes(storageLimitBytes)} plan`} />
        <SummaryCard icon={FileText} label="Chunks indexed" value={totalChunks.toLocaleString()} sub={`${docsUploaded} sources`} />
        <SummaryCard icon={MessageSquare} label="Queries this month" value={totalQueries.toLocaleString()} sub="queries executed" />
        <SummaryCard icon={Gauge} label="Document quota" value={usageData?.document_quota === -1 ? "Unlimited" : `${docsUploaded}/${usageData?.document_quota ?? "—"}`} sub="uploaded documents" />
      </div>

      <div className="w-full h-2 bg-stone-100 rounded-full overflow-hidden mb-8">
        <div className={`h-full rounded-full ${storagePct > 90 ? "bg-rose-400" : storagePct > 70 ? "bg-amber-400" : "bg-indigo-400"}`} style={{ width: `${storagePct}%` }} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="border border-stone-100 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-stone-50 text-[11.5px] font-medium text-stone-400 uppercase tracking-wide">Overview</div>
          {perCollection.map((c) => (
            <div key={c.id} className="flex items-center justify-between px-4 py-2.5 border-t border-stone-100 text-[13px]">
              <div className="flex items-center gap-2 min-w-0">
                <Folder className="w-3.5 h-3.5 text-stone-400 shrink-0" />
                <span className="text-stone-700 truncate">{c.name}</span>
                <span className="text-stone-400 shrink-0">· {c.files} files</span>
              </div>
              <div className="flex items-center gap-3 text-stone-500 shrink-0">
                <span>{formatBytes(c.storage)}</span>
                <span className="w-16 text-right font-medium text-stone-700">{c.queries} q</span>
              </div>
            </div>
          ))}
        </div>

        <div className="border border-stone-100 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-stone-50 text-[11.5px] font-medium text-stone-400 uppercase tracking-wide">Quotas</div>
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-stone-100 text-[13px]">
            <span className="text-stone-700">Queries</span>
            <span className="text-stone-500">{totalQueries} / {usageData?.query_quota === -1 ? "∞" : usageData?.query_quota ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-stone-100 text-[13px]">
            <span className="text-stone-700">Documents</span>
            <span className="text-stone-500">{docsUploaded} / {usageData?.document_quota === -1 ? "∞" : usageData?.document_quota ?? "—"}</span>
          </div>
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-stone-100 text-[13px]">
            <span className="text-stone-700">Chunks</span>
            <span className="text-stone-500">{totalChunks.toLocaleString()} / {usageData?.chunk_quota === -1 ? "∞" : usageData?.chunk_quota?.toLocaleString() ?? "—"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function RagFileManager({ onOpenInbox, plan, onUpgrade, onDowngrade, view, setView, files, setFiles, onTagDoc, usageData, setUsageData }) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [isDragging, setIsDragging] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [uploading, setUploading] = useState(false);
  const prevStatusRef = useRef({});
  const pollingRef = useRef({});
  const inputRef = useRef(null);
  const mounted = useMountedFade();

  const pollDocumentStatus = useCallback((docId) => {
    if (pollingRef.current[docId]) return;
    pollingRef.current[docId] = true;

    const poll = async () => {
      try {
        const status = await getDocumentStatus(docId);
        const mappedStatus = status.status === "completed" ? "indexed" : status.status;
        setFiles((prev) => prev.map((f) => (f.id === docId ? { ...f, status: mappedStatus } : f)));

        if (status.status !== "completed" && status.status !== "failed") {
          setTimeout(poll, 2000);
        } else {
          delete pollingRef.current[docId];
        }
      } catch {
        delete pollingRef.current[docId];
      }
    };
    setTimeout(poll, 1500);
  }, [setFiles]);

  const addFiles = useCallback(
    async (fileList) => {
      const selected = Array.from(fileList);
      if (selected.length === 0) return;

      setUploading(true);
      try {
        for (const file of selected) {
          const doc = await uploadDocument(file);
          const mapped = mapDocumentToFrontend(doc);
          mapped.status = "processing";
          mapped.progress = 0;
          setFiles((prev) => [mapped, ...prev]);
          pollDocumentStatus(doc.id);
        }
      } catch (err) {
        console.error("Upload failed:", err);
      } finally {
        setUploading(false);
      }
    },
    [setFiles, pollDocumentStatus]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  };

  const onRetry = (id) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, status: "processing", progress: 0, error: null } : f)));
    pollDocumentStatus(id);
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = (visibleFiles) => {
    setSelectedIds((prev) => {
      const allSelected = visibleFiles.every((f) => prev.has(f.id));
      const next = new Set(prev);
      visibleFiles.forEach((f) => (allSelected ? next.delete(f.id) : next.add(f.id)));
      return next;
    });
  };

  const requestDelete = (fileOrFiles) => setDeleteTarget(fileOrFiles);
  const cancelDelete = () => setDeleteTarget(null);

  const confirmDelete = async () => {
    const ids = Array.isArray(deleteTarget) ? deleteTarget.map((f) => f.id) : [deleteTarget.id];
    try {
      await Promise.all(ids.map((id) => deleteDocument(id)));
      setFiles((prev) => prev.filter((f) => !ids.includes(f.id)));
      setSelectedIds((prev) => {
        const next = new Set(prev);
        ids.forEach((id) => next.delete(id));
        return next;
      });
    } catch (err) {
      console.error("Delete failed:", err);
    }
    setDeleteTarget(null);
  };

  const filtered = files.filter((f) => {
    const matchesQuery = f.name.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = statusFilter === "all" || f.status === statusFilter;
    return matchesQuery && matchesStatus;
  });

  const statusCounts = files.reduce((acc, f) => {
    acc[f.status] = (acc[f.status] || 0) + 1;
    return acc;
  }, {});

  const uploadLimit = PLANS[plan].uploadLimit;
  const uploadLimitReached = plan === "free" && files.length >= uploadLimit;

  return (
    <div className={`h-full w-full bg-white text-stone-900 flex transition-opacity duration-200 ${mounted ? "opacity-100" : "opacity-0"}`}>
      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        <header className="px-8 pt-6 pb-0 border-b border-stone-100 shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-[18px] font-semibold tracking-tight">Knowledge Sources</h1>
              <p className="text-[13px] text-stone-500 mt-0.5 mb-4">Files uploaded here are chunked, embedded, and made retrievable to the assistant.</p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            {[
              { id: "sources", label: "Sources" },
              { id: "usage", label: "Usage" },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setView(t.id)}
                className={`text-[13.5px] font-medium pb-3 border-b-2 transition-colors ${
                  view === t.id ? "border-stone-900 text-stone-900" : "border-transparent text-stone-400 hover:text-stone-600"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </header>

        {view === "usage" ? (
          <UsageView files={files} plan={plan} onUpgrade={onUpgrade} onDowngrade={onDowngrade} usageData={usageData} />
        ) : (
          <>
            <div className="px-8 py-5 shrink-0">
              {uploadLimitReached ? (
                <UpgradeLockBar
                  icon={UploadCloud}
                  title={`You've reached the ${uploadLimit}-source limit on the Free plan`}
                  subtitle="Upgrade to Pro for unlimited indexed sources."
                  onUpgrade={onUpgrade}
                />
              ) : (
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={onDrop}
                  className={`rounded-xl border-2 border-dashed flex flex-col items-center justify-center py-7 transition-colors ${
                    isDragging ? "border-indigo-400 bg-indigo-50/60" : "border-stone-200 hover:border-stone-300"
                  }`}
                >
                  <input ref={inputRef} type="file" multiple className="hidden" onChange={(e) => e.target.files?.length && addFiles(e.target.files)} />
                  <div className="w-11 h-11 rounded-full bg-indigo-50 flex items-center justify-center mb-3">
                    {uploading ? <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" /> : <UploadCloud className="w-5 h-5 text-indigo-500" />}
                  </div>
                  <p className="text-[14px] font-medium text-stone-700">{uploading ? "Uploading…" : "Drop files to add to the index"}</p>
                  <p className="text-[12.5px] text-stone-400 mt-1 mb-4">PDF, DOCX, CSV, PPTX, or Excel · up to 200 MB each</p>

                  <button onClick={() => inputRef.current?.click()} className="text-[12.5px] font-medium bg-stone-900 text-white rounded-lg px-3 py-1.5 hover:bg-stone-800">
                    Browse files
                  </button>
                </div>
              )}
            </div>

            <div className="px-8 pb-3 flex items-center gap-2 shrink-0">
              <div className="flex items-center gap-2 bg-stone-100 rounded-lg px-3 py-2 w-64">
                <Search className="w-4 h-4 text-stone-400 shrink-0" />
                <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search files" className="bg-transparent text-[13px] outline-none w-full placeholder:text-stone-400" />
              </div>
              {["all", "indexed", "processing", "failed"].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`text-[12.5px] font-medium px-3 py-1.5 rounded-full border transition-colors ${
                    statusFilter === s ? "bg-stone-900 text-white border-stone-900" : "border-stone-200 text-stone-500 hover:bg-stone-50"
                  }`}
                >
                  {s === "all" ? "All" : STATUS_CONFIG[s]?.label || s}
                  {s !== "all" && statusCounts[s] ? ` (${statusCounts[s]})` : ""}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto px-8 pb-24 relative">
              <div className="border border-stone-100 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 pl-4 pr-3 py-1.5 bg-stone-50 text-[11px] font-medium text-stone-400 uppercase tracking-wide">
                  <input
                    type="checkbox"
                    checked={filtered.length > 0 && filtered.every((f) => selectedIds.has(f.id))}
                    onChange={() => toggleSelectAll(filtered)}
                    className="w-3.5 h-3.5 rounded border-stone-300 text-indigo-600 focus:ring-indigo-400 cursor-pointer shrink-0"
                    style={{ width: 14 }}
                  />
                  <div style={{ width: 24 }} className="shrink-0" />
                  <div className="flex-1 min-w-0">Source</div>
                  <div style={{ width: 100 }} className="shrink-0">Status</div>
                  <div style={{ width: 80 }} className="shrink-0 text-right">Size</div>
                  <div style={{ width: 90 }} className="shrink-0 text-right">Chunks</div>
                  <div style={{ width: 64 }} className="shrink-0 text-right">Updated</div>
                  <div style={{ width: 138 }} className="shrink-0 text-right">Chat</div>
                </div>
                {filtered.length === 0 ? (
                  <div className="py-14 text-center text-[13px] text-stone-400">
                    {files.length === 0 ? "No files uploaded yet. Drop a file above to get started." : "No files match this filter."}
                  </div>
                ) : (
                  filtered.map((file) => (
                    <FileRow key={file.id} file={file} selected={selectedIds.has(file.id)} onToggleSelect={toggleSelect} onRetry={onRetry} onRequestDelete={requestDelete} onChat={onTagDoc} />
                  ))
                )}
              </div>
            </div>

            {selectedIds.size > 0 && (
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-stone-900 text-white rounded-full pl-4 pr-2 py-2 flex items-center gap-3 shadow-lg z-10">
                <span className="text-[13px]">{selectedIds.size} selected</span>
                <button onClick={() => requestDelete(files.filter((f) => selectedIds.has(f.id)))} className="flex items-center gap-1.5 text-[12.5px] font-medium bg-rose-500 hover:bg-rose-600 rounded-full px-3 py-1.5">
                  <Trash2 className="w-3.5 h-3.5" />
                  Delete
                </button>
                <button onClick={() => setSelectedIds(new Set())} className="w-6 h-6 rounded-full hover:bg-white/10 flex items-center justify-center">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </>
        )}
      </main>

      <DeleteConfirmModal target={deleteTarget} onCancel={cancelDelete} onConfirm={confirmDelete} />
    </div>
  );
}
