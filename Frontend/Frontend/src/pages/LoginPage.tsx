import { useState, type ChangeEvent } from "react";
import { Mail, Lock, FileText, Quote, type LucideIcon } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const colors = {
  ink: "#12182B",
  paper: "#FFFFFF",
  mist: "#F4F5F7",
  slate: "#6B7280",
  highlight: "#F4B400",
  line: "#E3E5EA",
};

export default function LoginPage() {
  const { login, register } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const set = (field: string) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isSignUp) {
        if (form.password !== form.confirm_password) {
          setError("Passwords do not match");
          setLoading(false);
          return;
        }
        await register(form);
      } else {
        await login(form.email, form.password);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row" style={{ fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,500;0,600;1,500&family=Inter:wght@400;500;600&display=swap');
        .ds-input {
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .ds-input:focus {
          outline: none;
          border-color: ${colors.highlight};
          box-shadow: 0 0 0 3px rgba(244, 180, 0, 0.22);
        }
      `}</style>

      {/* Left panel — the product's actual promise, shown rather than described */}
      <div
        className="w-full md:w-1/2 flex flex-col justify-between px-8 py-10 md:px-14 md:py-14"
        style={{ backgroundColor: colors.ink }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-md flex items-center justify-center"
            style={{ backgroundColor: colors.highlight }}
          >
            <FileText className="w-4 h-4" style={{ color: colors.ink }} strokeWidth={2.3} />
          </div>
          <span style={{ fontFamily: "'Source Serif 4', serif", color: "#FFFFFF", fontSize: "18px" }}>
            DocSense
          </span>
        </div>

        <div className="my-12 md:my-0 max-w-sm">
          <h1
            style={{
              fontFamily: "'Source Serif 4', serif",
              color: "#F5F6F8",
              fontSize: "38px",
              lineHeight: "1.2",
              fontWeight: 400,
            }}
          >
            Every answer traces back to a page.
          </h1>
          <p className="mt-4" style={{ color: "#9AA1B0", fontSize: "15px", lineHeight: "1.6" }}>
            Ask your documents a question. Get a direct answer — or nothing at
            all if the evidence isn't there.
          </p>
        </div>

        {/* The grounding moment, made concrete instead of described */}
        <div
          className="hidden sm:block rounded-lg p-5 max-w-sm"
          style={{ backgroundColor: "#1B2338", border: "1px solid #2A3350" }}
        >
          <p style={{ color: "#9AA1B0", fontSize: "13px", lineHeight: "1.65" }}>
            "...completed a six-month internship focused on{" "}
            <span
              style={{
                backgroundColor: colors.highlight,
                color: colors.ink,
                padding: "0 4px",
                borderRadius: "2px",
              }}
            >
              distributed systems and backend performance tuning
            </span>
            , working directly with the platform team."
          </p>
          <div className="mt-3 flex items-center gap-1.5" style={{ color: "#6B7280", fontSize: "12px" }}>
            <Quote className="w-3 h-3" />
            <span>resume.pdf · page 2</span>
          </div>
        </div>
      </div>

      {/* Right panel — the form, kept quiet */}
      <div
        className="w-full md:w-1/2 flex items-center justify-center px-6 py-14 md:px-14"
        style={{ backgroundColor: colors.paper }}
      >
        <div className="w-full max-w-sm">
          <h2 style={{ color: colors.ink, fontSize: "22px", fontWeight: 600 }}>
            {isSignUp ? "Create your account" : "Sign in to your account"}
          </h2>
          <p className="mt-1.5" style={{ color: colors.slate, fontSize: "14px" }}>
            {isSignUp
              ? "Start asking questions grounded in your own documents."
              : "Welcome back — pick up where you left off."}
          </p>

          {error && (
            <div
              className="mt-5 px-3.5 py-2.5 rounded-md"
              style={{
                backgroundColor: "#FDF0EF",
                border: "1px solid #F3D2D0",
                color: "#B3261E",
                fontSize: "13px",
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {isSignUp && (
              <div className="grid grid-cols-2 gap-3">
                <Field label="First name" value={form.first_name} onChange={set("first_name")} />
                <Field label="Last name" value={form.last_name} onChange={set("last_name")} />
              </div>
            )}

            <Field label="Email" type="email" icon={Mail} value={form.email} onChange={set("email")} />
            <Field
              label="Password"
              type="password"
              icon={Lock}
              value={form.password}
              onChange={set("password")}
              minLength={8}
            />
            {isSignUp && (
              <Field
                label="Confirm password"
                type="password"
                value={form.confirm_password}
                onChange={set("confirm_password")}
                minLength={8}
              />
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-md mt-2"
              style={{
                backgroundColor: colors.ink,
                color: "#FFFFFF",
                fontSize: "14px",
                fontWeight: 500,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? "default" : "pointer",
              }}
            >
              {loading ? "Please wait…" : isSignUp ? "Create account" : "Sign in"}
            </button>
          </form>

          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError("");
            }}
            className="mt-6"
            style={{ color: colors.ink, fontSize: "13.5px", fontWeight: 500 }}
          >
            {isSignUp ? "Already have an account? " : "Don't have an account? "}
            <span
              style={{
                textDecoration: "underline",
                textDecorationColor: colors.highlight,
                textUnderlineOffset: "3px",
              }}
            >
              {isSignUp ? "Sign in" : "Sign up"}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  type = "text",
  icon: Icon,
  value,
  onChange,
  minLength,
}: {
  label: string;
  type?: string;
  icon?: LucideIcon;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  minLength?: number;
}) {
  return (
    <div>
      <label className="block mb-1.5" style={{ color: colors.ink, fontSize: "13px", fontWeight: 500 }}>
        {label}
      </label>
      <div className="relative">
        {Icon && (
          <Icon
            className="absolute top-1/2 -translate-y-1/2 w-4 h-4"
            style={{ left: "12px", color: colors.slate }}
          />
        )}
        <input
          type={type}
          required
          minLength={minLength}
          value={value}
          onChange={onChange}
          className="ds-input w-full py-2.5 rounded-md"
          style={{
            paddingLeft: Icon ? "36px" : "14px",
            paddingRight: "14px",
            backgroundColor: colors.mist,
            border: `1px solid ${colors.line}`,
            color: colors.ink,
            fontSize: "14px",
          }}
        />
      </div>
    </div>
  );
}