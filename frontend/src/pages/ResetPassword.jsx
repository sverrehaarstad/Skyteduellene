import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { Target } from "@/components/Target";
import { toast } from "sonner";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Passordene er ikke like"); return; }
    setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, password });
      toast.success("Passordet er endret – logg inn med nytt passord");
      navigate("/login", { replace: true });
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
          <h1 className="text-3xl font-black tracking-tight text-slate-900 mt-4" style={{ fontFamily: "Outfit, sans-serif" }}>Nytt passord</h1>
        </div>
        {!token ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 text-center" data-testid="reset-no-token">
            <p className="text-slate-600">Ugyldig lenke. Be om en ny tilbakestillingslenke.</p>
            <Link to="/glemt-passord" className="inline-block mt-3 text-sm font-semibold text-[#D92525] hover:underline">Glemt passord</Link>
          </div>
        ) : (
          <form onSubmit={submit} className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4" data-testid="reset-form">
            {error && <div className="text-sm text-[#D92525] bg-[#FEF2F2] border border-[#FCA5A5] rounded-lg px-3 py-2" data-testid="reset-error">{error}</div>}
            <div>
              <label className="text-sm font-semibold text-slate-700">Nytt passord (min. 6 tegn)</label>
              <input data-testid="reset-password" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525] focus:ring-1 focus:ring-[#D92525]" />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">Gjenta passord</label>
              <input data-testid="reset-confirm" type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)}
                className="mt-1 w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525] focus:ring-1 focus:ring-[#D92525]" />
            </div>
            <button data-testid="reset-submit" disabled={busy} className="w-full py-2.5 bg-[#D92525] hover:bg-[#B91C1C] text-white font-bold rounded-lg transition-colors disabled:opacity-60">
              {busy ? "Lagrer..." : "Lagre nytt passord"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
