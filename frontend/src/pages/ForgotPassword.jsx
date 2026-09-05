import { useState } from "react";
import { Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { Target } from "@/components/Target";
import { MailCheck } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/auth/forgot-password", { email, origin: window.location.origin });
      setSent(true);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <Target size={48} />
          <h1 className="text-3xl font-black tracking-tight text-slate-900 mt-4" style={{ fontFamily: "Outfit, sans-serif" }}>Glemt passord</h1>
          <p className="text-slate-500 text-sm mt-1 text-center">Skriv inn e-posten din, så sender vi en tilbakestillingslenke.</p>
        </div>

        {sent ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center" data-testid="forgot-sent">
            <MailCheck size={40} className="mx-auto text-[#16A34A] mb-3" />
            <p className="font-semibold text-slate-900">Sjekk innboksen din</p>
            <p className="text-sm text-slate-500 mt-1">Hvis e-posten finnes hos oss, har vi sendt en lenke for å velge nytt passord. Lenken er gyldig i 1 time.</p>
            <Link to="/login" className="inline-block mt-4 text-sm font-semibold text-[#D92525] hover:underline">Tilbake til innlogging</Link>
          </div>
        ) : (
          <form onSubmit={submit} className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4" data-testid="forgot-form">
            {error && <div className="text-sm text-[#D92525] bg-[#FEF2F2] border border-[#FCA5A5] rounded-lg px-3 py-2" data-testid="forgot-error">{error}</div>}
            <div>
              <label className="text-sm font-semibold text-slate-700">E-post</label>
              <input data-testid="forgot-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525] focus:ring-1 focus:ring-[#D92525]" />
            </div>
            <button data-testid="forgot-submit" disabled={busy} className="w-full py-2.5 bg-[#D92525] hover:bg-[#B91C1C] text-white font-bold rounded-lg transition-colors disabled:opacity-60">
              {busy ? "Sender..." : "Send tilbakestillingslenke"}
            </button>
            <p className="text-center text-sm text-slate-500">
              <Link to="/login" className="font-semibold text-[#D92525] hover:underline">Tilbake til innlogging</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
