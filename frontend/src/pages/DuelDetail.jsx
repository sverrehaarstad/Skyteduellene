import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ShooterAvatar } from "@/components/ShooterAvatar";
import { toast } from "sonner";
import { ArrowLeft, MapPin, Clock, BarChart3, Check } from "lucide-react";

const outcomeLabel = (d) =>
  d.outcome === "1" ? d.shooter1 : d.outcome === "2" ? d.shooter2 : "Uavgjort";

export default function DuelDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, refreshMe } = useAuth();
  const [duel, setDuel] = useState(null);
  const [myPick, setMyPick] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get(`/duels/${id}`);
      setDuel(data);
      if (user) {
        const res = await api.get("/my-tips");
        const mine = res.data.find((t) => t.duel.id === id);
        setMyPick(mine ? mine.pick : null);
      }
    } catch {
      setNotFound(true);
    }
  }, [id, user]);

  useEffect(() => { load(); }, [load]);

  const placeTip = async (choice) => {
    if (!user) { toast.error("Du må logge inn for å tippe"); navigate("/login"); return; }
    setSaving(true);
    try {
      await api.post(`/duels/${id}/tip`, { pick: choice });
      setMyPick(choice);
      toast.success("Tips lagret!");
      load();
      refreshMe();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setSaving(false);
    }
  };

  if (notFound) return (
    <div className="max-w-2xl mx-auto px-4 py-16 text-center">
      <p className="text-slate-500 font-semibold">Fant ikke duellen.</p>
      <Link to="/" className="text-[#D92525] font-semibold hover:underline mt-2 inline-block">Tilbake til dueller</Link>
    </div>
  );
  if (!duel) return <div className="max-w-2xl mx-auto px-4 py-16 text-slate-500">Laster...</div>;

  const tc = duel.tip_counts || { "1": 0, X: 0, "2": 0 };
  const total = tc["1"] + tc["X"] + tc["2"];
  const pct = (n) => (total ? Math.round((n / total) * 100) : 0);
  const isOpen = duel.status === "open";

  const bars = [
    { key: "1", label: duel.shooter1, sub: "Skytter 1", n: tc["1"] },
    { key: "X", label: "Uavgjort", sub: "Uavgjort", n: tc["X"] },
    { key: "2", label: duel.shooter2, sub: "Skytter 2", n: tc["2"] },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6" data-testid="duel-detail">
      <button onClick={() => navigate(-1)} data-testid="back-btn" className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-900 mb-5">
        <ArrowLeft size={16} /> Tilbake
      </button>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-6">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#B91C1C] bg-[#FEF2F2] px-2.5 py-1 rounded-full">{duel.discipline}</span>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${isOpen ? "bg-green-50 text-[#16A34A]" : "bg-slate-100 text-slate-600"}`}>
            {isOpen ? "Åpen for tipping" : "Avsluttet"}
          </span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 flex flex-col items-center text-center">
            <ShooterAvatar src={duel.shooter1_img} name={duel.shooter1} badge="1" size="lg" />
            <p className="font-bold text-slate-900 mt-3">{duel.shooter1}</p>
            {!isOpen && <p className="font-mono text-2xl text-slate-900 mt-1">{duel.score1 || "-"}</p>}
          </div>
          <div className="text-slate-300 font-black text-lg" style={{ fontFamily: "Outfit, sans-serif" }}>VS</div>
          <div className="flex-1 flex flex-col items-center text-center">
            <ShooterAvatar src={duel.shooter2_img} name={duel.shooter2} badge="2" size="lg" />
            <p className="font-bold text-slate-900 mt-3">{duel.shooter2}</p>
            {!isOpen && <p className="font-mono text-2xl text-slate-900 mt-1">{duel.score2 || "-"}</p>}
          </div>
        </div>

        {(duel.venue || duel.start_time) && (
          <div className="flex items-center justify-center gap-5 text-sm text-slate-500 mt-6">
            {duel.venue && <span className="flex items-center gap-1.5"><MapPin size={14} /> {duel.venue}</span>}
            {duel.start_time && <span className="flex items-center gap-1.5"><Clock size={14} /> {duel.start_time}</span>}
          </div>
        )}

        {!isOpen && (
          <div className="text-center mt-6">
            <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Vinner</span>
            <span className="inline-block px-4 py-1.5 rounded-full bg-[#0F172A] text-white font-bold" style={{ fontFamily: "Outfit, sans-serif" }} data-testid="detail-winner">
              {outcomeLabel(duel)}
            </span>
          </div>
        )}

        {/* Tipping */}
        {isOpen && (
          <div className="grid grid-cols-3 gap-2 mt-8">
            {[["1", duel.shooter1.split(" ")[0]], ["X", "Uavgjort"], ["2", duel.shooter2.split(" ")[0]]].map(([val, sub]) => (
              <button key={val} onClick={() => placeTip(val)} disabled={saving} data-testid={`detail-tip-${val}`}
                className={`flex flex-col items-center py-4 rounded-xl border transition-colors duration-200 ${
                  myPick === val ? "bg-[#D92525] border-[#D92525] text-white shadow-sm" : "bg-white border-slate-200 text-slate-800 hover:border-[#FCA5A5] hover:bg-[#FEF2F2]"
                }`}>
                <span className="font-black text-xl" style={{ fontFamily: "Outfit, sans-serif" }}>{val === "X" ? "U" : val}</span>
                <span className={`text-[11px] font-semibold uppercase tracking-wider mt-1 ${myPick === val ? "text-red-100" : "text-slate-500"}`}>{sub}</span>
              </button>
            ))}
          </div>
        )}
        {myPick && isOpen && <p className="text-center text-xs text-[#16A34A] font-semibold mt-3 flex items-center justify-center gap-1"><Check size={12} /> Ditt tips er registrert</p>}
      </div>

      {/* Tip distribution */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 mt-5" data-testid="tip-distribution">
        <h2 className="flex items-center gap-2 font-bold text-slate-900 mb-4"><BarChart3 size={18} className="text-[#D92525]" /> Tippefordeling ({total} tips)</h2>
        <div className="space-y-4">
          {bars.map((b) => (
            <div key={b.key}>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-semibold text-slate-700"><span className="font-mono text-slate-400 mr-1.5">{b.key === "X" ? "U" : b.key}</span>{b.label}</span>
                <span className="font-mono text-slate-500">{pct(b.n)}% · {b.n}</span>
              </div>
              <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                <div className="h-full rounded-full bg-[#D92525] transition-[width] duration-500" style={{ width: `${pct(b.n)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
