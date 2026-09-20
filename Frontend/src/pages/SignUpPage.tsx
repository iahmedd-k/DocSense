import { SignUp } from "@clerk/react";
import { Database, Sparkles } from "lucide-react";

export default function SignUpPage() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-stone-50 px-4 py-12 font-[system-ui]">
      <div className="w-full max-w-[440px] flex flex-col items-center">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-11 h-11 rounded-xl bg-indigo-600 shadow-md shadow-indigo-500/20 flex items-center justify-center mb-3">
            <Database className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-[22px] font-bold text-stone-900 tracking-tight flex items-center gap-1.5">
            DocSense
          </h1>
          <p className="text-[13px] text-stone-500 mt-1 max-w-[300px]">
            Create your document intelligence workspace
          </p>
        </div>

        {/* Auth Card */}
        <div className="w-full bg-white rounded-2xl border border-stone-200/80 shadow-sm p-6 sm:p-7">
          <SignUp
            routing="path"
            path="/signup"
            signInUrl="/login"
            fallbackRedirectUrl="/"
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "shadow-none border-none p-0 bg-transparent",
                headerTitle: "text-[18px] font-semibold text-stone-900 text-center",
                headerSubtitle: "text-[13px] text-stone-500 text-center",
                formButtonPrimary:
                  "bg-indigo-600 hover:bg-indigo-700 text-white text-[13.5px] font-medium py-2.5 rounded-lg transition-colors shadow-sm cursor-pointer",
                formFieldInput:
                  "rounded-lg border-stone-200 text-[13.5px] focus:border-indigo-500 focus:ring-indigo-500",
                footerActionLink: "text-indigo-600 hover:text-indigo-700 font-medium",
                identityPreviewText: "text-stone-700 text-[13px]",
                identityPreviewEditButton: "text-indigo-600 hover:text-indigo-700",
              },
            }}
          />
        </div>

        {/* Demo Notice Footer */}
        <div className="mt-6 text-center">
          <p className="text-[12px] text-stone-400 flex items-center justify-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Interactive Portfolio Demonstration
          </p>
        </div>
      </div>
    </div>
  );
}
