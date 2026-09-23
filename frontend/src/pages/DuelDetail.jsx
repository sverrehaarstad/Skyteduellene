import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ShooterAvatar } from "@/components/ShooterAvatar";
import { Countdown } from "@/components/Countdown";
import { toast } from "sonner";
import { ArrowLeft, MapPin, Clock, Check, Share2, Trophy } from "lucide-react";

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
        const mine = res.data.find((t) => t.duel.id === Number(id));
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
  const deleteTip = async () => {
  if (!myPick) return;

  setSaving(true);

  try {
    await api.delete(`/duels/${id}/tip`);
    setMyPick(null);
    toast.success("Tipset er slettet");
    load();
    refreshMe();
  } catch (e) {
    toast.error(formatApiError(e.response?.data?.error));
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

  const isOpen = duel.status === "open";
  const tc = duel.tip_counts || { "1": 0, X: 0, "2": 0 };
  const totalTips = tc["1"] + tc["X"] + tc["2"];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6" data-testid="duel-detail">
      <div className="flex items-center justify-between mb-5">
        <button onClick={() => navigate(-1)} data-testid="back-btn" className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-900">
          <ArrowLeft size={16} /> Tilbake
        </button>
        <ShareButton duel={duel} />
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-6">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#B91C1C] bg-[#FEF2F2] px-2.5 py-1 rounded-full">{duel.discipline}</span>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${isOpen ? "bg-green-50 text-[#16A34A]" : "bg-slate-100 text-slate-600"}`}>
            {isOpen ? "Åpen for tipping" : "Avsluttet"}
          </span>
        </div>

        {duel.tournament_id && (
          <Link to={`/serie/${duel.tournament_id}`} data-testid="detail-tournament-link" className="flex items-center justify-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-[#D92525] transition-colors mb-4 -mt-2">
            <Trophy size={14} className="text-[#EAB308]" /> {duel.tournament_name}
          </Link>
        )}

        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 flex flex-col items-center text-center">
            <ShooterAvatar src={duel.shooter1_img} name={duel.shooter1} badge="1" size="lg" />
            <Link to={`/skytter/${encodeURIComponent(duel.shooter1)}`} data-testid="shooter1-link" className="font-bold text-slate-900 mt-3 hover:text-[#D92525] transition-colors">
  {duel.shooter1}
</Link>
{duel.shooter1_club && (
  <p className="text-sm text-slate-500 mt-1">{duel.shooter1_club}</p>
)}
{duel.shooter1_class && (
  <p className="text-sm text-slate-500">Klasse {duel.shooter1_class}</p>
)}
            {!isOpen && <p className="font-mono text-2xl text-slate-900 mt-1">{duel.score1 || "-"}</p>}
          </div>
          <div className="text-slate-300 font-black text-lg" style={{ fontFamily: "Outfit, sans-serif" }}>VS</div>
          <div className="flex-1 flex flex-col items-center text-center">
            <ShooterAvatar src={duel.shooter2_img} name={duel.shooter2} badge="2" size="lg" />
            <Link to={`/skytter/${encodeURIComponent(duel.shooter2)}`} data-testid="shooter2-link" className="font-bold text-slate-900 mt-3 hover:text-[#D92525] transition-colors">
  {duel.shooter2}
</Link>
{duel.shooter2_club && (
  <p className="text-sm text-slate-500 mt-1">{duel.shooter2_club}</p>
)}
{duel.shooter2_class && (
  <p className="text-sm text-slate-500">Klasse {duel.shooter2_class}</p>
)}
            {!isOpen && <p className="font-mono text-2xl text-slate-900 mt-1">{duel.score2 || "-"}</p>}
          </div>
        </div>

        {(duel.venue || duel.start_time) && (
          <div className="flex items-center justify-center gap-5 text-sm text-slate-500 mt-6">
            {duel.venue && <span className="flex items-center gap-1.5"><MapPin size={14} /> {duel.venue}</span>}
            {duel.start_time && <span className="flex items-center gap-1.5"><Clock size={14} /> {duel.start_time}</span>}
          </div>
        )}

        {isOpen && duel.start_at && (
          <div className="flex flex-col items-center mt-6" data-testid="detail-countdown">
            <p className="text-xs uppercase tracking-wider text-slate-400 mb-1">Starter om</p>
            <Countdown startAt={duel.start_at} className="text-lg" />
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
        <div className="text-center mt-4">
  <p className="text-sm text-slate-500">
    Total tips: <span className="font-semibold text-slate-700">{totalTips}</span>
  </p>
</div>

        {/* Tipping */}
        {isOpen && (
          <div className="grid grid-cols-3 gap-2 mt-8">
            {[["1", duel.shooter1.split(" ")[0]], ["X", "ved lik poengsum"], ["2", duel.shooter2.split(" ")[0]]].map(([val, sub]) => (
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
        {myPick && isOpen && (
  <div className="text-center mt-3">
    <p className="text-xs text-[#16A34A] font-semibold flex items-center justify-center gap-1">
      <Check size={12} /> Ditt tips er registrert
    </p>

    <button
      type="button"
      onClick={deleteTip}
      disabled={saving}
      className="mt-1 text-xs font-semibold text-slate-400 hover:text-[#D92525] transition-colors disabled:opacity-50"
    >
      Slett tips
    </button>
  </div>
)}
      </div>


    </div>
  );
}


function ShareButton({ duel }) {
  const share = async () => {
    const url = window.location.href;
    const title = `${duel.shooter1} vs ${duel.shooter2} – Skyteduellene`;
    if (navigator.share) {
      try { await navigator.share({ title, text: "Tipp på denne duellen!", url }); return; } catch { /* cancelled */ }
    }
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Lenke kopiert – del den med venner!");
    } catch {
      toast.error("Kunne ikke kopiere lenken");
    }
  };
  return (
    <button onClick={share} data-testid="share-btn" className="flex items-center gap-1.5 text-sm font-semibold text-white bg-[#D92525] hover:bg-[#B91C1C] px-3 py-1.5 rounded-lg transition-colors">
      <Share2 size={15} /> Del
    </button>
  );
}
