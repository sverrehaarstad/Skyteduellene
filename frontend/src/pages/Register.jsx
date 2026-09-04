import { useState } from "react";
import { useNavigate, Link, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { Target } from "@/components/Target";

export default function Register() {
  const { user, setSession } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post("/auth/register", { name, email, password });
      setSession(data);
      navigate("/");
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
          <h1 className="text-3xl font-black tracking-tight text-slate-900 mt-4" style={{ fontFamily: "Outfit, sans-serif" }}>Registrer deg</h1>
          <p className="text-slate-500 text-sm mt-1">Bli med og tipp på duellene!</p>
        </div>
        <form onSubmit={submit} className="bg-white border border-slate-200 rounded-2xl p-6 space-y-4" data-testid="register-form">
          {error && <div className="text-sm text-[#D92525] bg-[#FEF2F2] border border-[#FCA5A5] rounded-lg px-3 py-2" data-testid="register-error">{error}</div>}
          <div>
            <label className="text-sm font-semibold text-slate-700">Visningsnavn</label>
            <input data-testid="register-name" required value={name} onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525] focus:ring-1 focus:ring-[#D92525]" />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">E-post</label>
            <input data-testid="register-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525] focus:ring-1 focus:ring-[#D92525]" />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Passord (min. 6 tegn)</label>
            <input data-testid="register-password" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525] focus:ring-1 focus:ring-[#D92525]" />
          </div>
          <button data-testid="register-submit" disabled={busy} className="w-full py-2.5 bg-[#D92525] hover:bg-[#B91C1C] text-white font-bold rounded-lg transition-colors disabled:opacity-60">
            {busy ? "Oppretter..." : "Opprett konto"}
          </button>
          <p className="text-center text-sm text-slate-500">
            Har du konto? <Link to="/login" className="font-semibold text-[#D92525] hover:underline">Logg inn</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
