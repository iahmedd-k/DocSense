import { SignIn } from "@clerk/react";
import { Database, Lock, CheckCircle2 } from "lucide-react";

function BrandMark({ tone = "dark" }: { tone?: string }) {
  const isDark = tone === "dark";
  return (
    <div className="flex items-center gap-2.5">
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
          isDark ? "bg-blue-500 shadow-md shadow-blue-500/20" : "bg-slate-900"
        }`}
      >
        <Database className="w-4 h-4 text-white" />
      </div>
      <span className={`text-[15px] font-semibold tracking-tight ${isDark ? "text-white" : "text-slate-900"}`}>
        DocSense
      </span>
    </div>
  );
}

const TRUST_POINTS = [
  {
    icon: Lock,
    title: "Role-based access",
    body: "Every collection and document inherits your org's permission model.",
  },
  {
    icon: Database,
    title: "Source-grounded answers",
    body: "Every response cites the exact document and chunk it came from.",
  },
  {
    icon: CheckCircle2,
    title: "Audit-ready",
    body: "Full trail of what was ingested, queried, and by whom.",
  },
];

export default function LoginPage() {
  return (
    <div className="min-h-screen w-full flex bg-white font-[system-ui]">
      {/* Brand panel */}
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

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-10 overflow-y-auto">
        <div className="w-full max-w-[420px] flex flex-col items-center">
          <div className="mb-6 flex lg:hidden">
            <BrandMark tone="light" />
          </div>

          <SignIn
            routing="path"
            path="/login"
            signUpUrl="/signup"
            fallbackRedirectUrl="/"
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "shadow-none border border-slate-200 rounded-xl p-6",
                headerTitle: "text-[19px] font-semibold text-slate-900",
                headerSubtitle: "text-[13px] text-slate-500",
                formButtonPrimary: "bg-slate-900 hover:bg-slate-800 text-white text-[13.5px] py-2.5 rounded-lg",
                footerActionLink: "text-blue-600 hover:text-blue-700 font-medium",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}