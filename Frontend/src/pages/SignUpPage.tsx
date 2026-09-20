import { SignUp } from "@clerk/react";
import { BrandLogo } from "../components/BrandLogo";

export default function SignUpPage() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-stone-50/70 p-4 font-[system-ui]">
      <div className="w-full max-w-[420px] flex flex-col items-center">
        {/* Brand Header */}
        <div className="mb-6 flex flex-col items-center">
          <BrandLogo size={42} showText={true} />
        </div>

        {/* Auth Card */}
        <div className="w-full">
          <SignUp
            routing="path"
            path="/signup"
            signInUrl="/login"
            fallbackRedirectUrl="/"
            appearance={{
              layout: {
                unsafe_disableDevelopmentModeWarnings: true,
                logoPlacement: "none",
              },
              elements: {
                rootBox: "w-full",
                card: "border border-stone-200/90 shadow-sm rounded-2xl bg-white p-6 sm:p-7 w-full",
                headerTitle: "hidden",
                headerSubtitle: "hidden",
                formButtonPrimary:
                  "bg-indigo-600 hover:bg-indigo-700 text-white text-[13.5px] font-semibold py-2.5 rounded-xl transition-all shadow-xs cursor-pointer",
                formFieldInput:
                  "rounded-xl border-stone-200 text-[13.5px] focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 py-2.5",
                formFieldLabel: "text-[12.5px] font-medium text-stone-700",
                footerActionLink: "text-indigo-600 hover:text-indigo-700 font-medium text-[13px]",
                dividerLine: "bg-stone-100",
                dividerText: "text-stone-400 text-[12px]",
                identityPreviewText: "text-stone-700 text-[13px] font-medium",
                identityPreviewEditButton: "text-indigo-600 hover:text-indigo-700 text-[12px]",
                formFieldAction: "text-indigo-600 hover:text-indigo-700 text-[12px]",
                socialButtonsBlockButton:
                  "border border-stone-200 hover:bg-stone-50 text-stone-700 rounded-xl py-2.5 text-[13px] font-medium transition-colors",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
