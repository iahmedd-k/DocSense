import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Database, Mail, Lock, User, Eye, EyeOff, AlertCircle, ArrowRight, Loader2, CheckCircle2, Github, Chrome, MessageSquare, Check } from "lucide-react";

function AuthField({ icon: Icon, type = "text", onEnter, ...props }: any) {
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
        <button type="button" onClick={() => setShow((v: boolean) => !v)} className="text-slate-400 hover:text-slate-600 shrink-0">
          {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      )}
    </div>
  );
}

function BrandMark({ tone = "dark" }: { tone?: string }) {
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

function PasswordStrength({ password }: { password: string }) {
  const [strength, setStrength] = useState(0);
  const [label, setLabel] = useState("");
  const [color, setColor] = useState("bg-slate-200");

  useEffect(() => {
    if (!password) {
      setStrength(0);
      setLabel("");
      setColor("bg-slate-200");
      return;
    }
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    
    setStrength(Math.min(score, 4) * 25);
    
    switch (score) {
      case 0:
      case 1:
        setLabel("Weak");
        setColor("bg-rose-500");
        break;
      case 2:
        setLabel("Fair");
        setColor("bg-amber-500");
        break;
      case 3:
        setLabel("Good");
        setColor("bg-lime-500");
        break;
      case 4:
        setLabel("Strong");
        setColor("bg-emerald-500");
        break;
      default:
        setLabel("");
        setColor("bg-slate-200");
    }
  }, [password]);

  return (
    <div className="space-y-1.5">
      <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <div className={`h-full transition-all duration-300 ease-out ${color}`} style={{ width: `${strength}%` }} />
      </div>
      <p className={`text-[11px] font-medium ${color.replace("bg-", "text-")}`}>
        {label ? `Password strength: ${label}` : "Password must be at least 8 characters"}
      </p>
    </div>
  );
}

const TRUST_POINTS = [
  { icon: Lock, title: "Role-based access", body: "Every collection and document inherits your org's permission model." },
  { icon: Database, title: "Source-grounded answers", body: "Every response cites the exact document and chunk it came from." },
  { icon: CheckCircle2, title: "Audit-ready", body: "Full trail of what was ingested, queried, and by whom." },
];

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (loading) return;
    if (!email.trim() || !email.includes("@")) return setError("Enter a valid work email.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err: any) {
      setError(err?.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (loading) return;
    if (!firstName.trim() || !lastName.trim()) return setError("Fill in your name to continue.");
    if (!email.trim() || !email.includes("@")) return setError("Enter a valid work email.");
    if (password.length < 8) return setError("Password must be at least 8 characters.");
    setError("");
    setLoading(true);
    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        confirm_password: password,
      });
      navigate("/", { replace: true });
    } catch (err: any) {
      setError(err?.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-full flex bg-white font-[system-ui]">
      {/* Brand panel */}
      <div className="hidden lg:flex lg:w-[440px] shrink-0 flex-col justify-between bg-slate-900 px-10 py-10">
        <BrandMark tone="dark" />
        <div>
          <h2 className="text-[24px] font-semibold text-white leading-snug max-w-[320px]">
            Enterprise search, grounded in your own documents.
          </h2>
          <p className="text-[13.5px] text-slate-400 mt-3 max-w-[320px] leading-relaxed">
            DocSense indexes your organization's files into governed collections and answers only from what's been approved for retrieval.
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
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-[360px]">
          <div className="mb-8 flex lg:hidden">
            <BrandMark tone="light" />
          </div>

          {mode === "login" ? (
            <>
              <h1 className="text-[19px] font-semibold text-slate-900">Sign in to your workspace</h1>
              <p className="text-[13px] text-slate-500 mt-1 mb-7">Use your work email to continue.</p>
              <div className="space-y-3">
                <AuthField icon={Mail} type="email" placeholder="Work email" value={email} onChange={(e: any) => { setEmail(e.target.value); setError(""); }} />
                <AuthField icon={Lock} type="password" placeholder="Password" value={password} onChange={(e: any) => { setPassword(e.target.value); setError(""); }} onEnter={handleLogin} />
                {error && (
                  <p className="flex items-center gap-1.5 text-[12px] text-rose-600">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />{error}
                  </p>
                )}
                <button onClick={handleLogin} disabled={loading} className="w-full flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-70 text-white text-[13.5px] font-medium rounded-lg py-2.5 mt-2 transition-colors">
                  {loading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Signing in…</> : <><span>Sign in</span><ArrowRight className="w-3.5 h-3.5" /></>}
                </button>
              </div>
              <p className="text-[13px] text-slate-500 text-center mt-6">
                Need a workspace?{" "}
                <button onClick={() => { setMode("signup"); setError(""); }} className="font-medium text-blue-600 hover:text-blue-700">Create one</button>
              </p>
            </>
          ) : (
            <>
              <h1 className="text-[19px] font-semibold text-slate-900">Set up your workspace</h1>
              <p className="text-[13px] text-slate-500 mt-1 mb-6">Create an admin account for your organization.</p>
              <div className="space-y-3">
                <AuthField icon={User} type="text" placeholder="First name" value={firstName} onChange={(e: any) => { setFirstName(e.target.value); setError(""); }} />
                <AuthField icon={User} type="text" placeholder="Last name" value={lastName} onChange={(e: any) => { setLastName(e.target.value); setError(""); }} />
                <AuthField icon={Mail} type="email" placeholder="Work email" value={email} onChange={(e: any) => { setEmail(e.target.value); setError(""); }} />
                <AuthField icon={Lock} type="password" placeholder="Password" value={password} onChange={(e: any) => { setPassword(e.target.value); setError(""); }} onEnter={handleRegister} />
                {error && (
                  <p className="flex items-center gap-1.5 text-[12px] text-rose-600">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />{error}
                  </p>
                )}
                <p className="text-[12px] text-slate-400 pt-1">By continuing, you agree to the Terms and Data Processing Agreement.</p>
                <button onClick={handleRegister} disabled={loading} className="w-full flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-70 text-white text-[13.5px] font-medium rounded-lg py-2.5 mt-2 transition-colors">
                  {loading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" />Creating workspace…</> : <><span>Create workspace</span><ArrowRight className="w-3.5 h-3.5" /></>}
                </button>
              </div>
              <p className="text-[13px] text-slate-500 text-center mt-6">
                Already have a workspace?{" "}
                <button onClick={() => { setMode("login"); setError(""); }} className="font-medium text-blue-600 hover:text-blue-700">Sign in</button>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
