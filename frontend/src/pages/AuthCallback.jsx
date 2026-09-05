import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Target } from "@/components/Target";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const processed = useRef(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const hash = window.location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    const sessionId = match ? decodeURIComponent(match[1]) : null;

    // Clear the hash so it isn't reprocessed
    window.history.replaceState(null, "", window.location.pathname);

    if (!sessionId) {
      navigate("/login", { replace: true });
      return;
    }

    (async () => {
      try {
        const { data } = await api.post("/auth/google", { session_id: sessionId, remember: true });
        setSession(data);
        navigate("/", { replace: true });
      } catch (e) {
        setError(formatApiError(e.response?.data?.detail) || "Innlogging feilet");
      }
    })();
  }, [navigate, setSession]);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center px-4">
      <Target size={48} className="animate-pulse" />
      {error ? (
        <>
          <p className="text-[#D92525] font-semibold mt-4" data-testid="callback-error">{error}</p>
          <button onClick={() => navigate("/login")} className="mt-3 text-sm font-semibold text-slate-600 hover:text-slate-900">Tilbake til innlogging</button>
        </>
      ) : (
        <p className="text-slate-500 font-semibold mt-4">Logger inn med Google...</p>
      )}
    </div>
  );
}
