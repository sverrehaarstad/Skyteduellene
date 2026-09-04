import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { ClipboardList, Check, X, Clock } from "lucide-react";

const pickLabel = (t) => (t.pick === "1" ? t.duel.shooter1 : t.pick === "2" ? t.duel.shooter2 : "Uavgjort");

const StatusBadge = ({ t }) => {
  if (t.duel.status !== "finished")
    return <span className="flex items-center gap-1 text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full"><Clock size={12} /> Venter</span>;
  if (t.correct)
    return <span className="flex items-center gap-1 text-xs font-semibold text-[#16A34A] bg-green-50 px-2.5 py-1 rounded-full"><Check size={12} /> Riktig +1</span>;
  return <span className="flex items-center gap-1 text-xs font-semibold text-[#D92525] bg-[#FEF2F2] px-2.5 py-1 rounded-full"><X size={12} /> Feil</span>;
};

export default function MyTips() {
  const { user } = useAuth();
  const [tips, setTips] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api.get("/my-tips").then(({ data }) => {
      setTips(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [user]);

  if (user === null) return null;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <ClipboardList size={22} className="text-[#D92525]" />
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Mine Tips</h1>
      </div>

      {loading ? (
        <p className="text-slate-500">Laster...</p>
      ) : tips.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-xl" data-testid="no-tips">
          <p className="text-slate-500 font-semibold">Du har ikke tippet ennå.</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="mytips-list">
          {tips.map((t) => (
            <div key={t.id} className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between gap-3" data-testid={`mytip-${t.id}`}>
              <div className="min-w-0">
                <p className="text-xs text-[#B91C1C] font-semibold uppercase tracking-wider">{t.duel.discipline}</p>
                <p className="font-bold text-slate-900 text-sm truncate">{t.duel.shooter1} vs {t.duel.shooter2}</p>
                <p className="text-xs text-slate-500 mt-0.5">Ditt tips: <span className="font-semibold text-slate-800">{pickLabel(t)}</span></p>
              </div>
              <StatusBadge t={t} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
