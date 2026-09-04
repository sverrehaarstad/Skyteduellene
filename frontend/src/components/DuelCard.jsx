import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { MapPin, Clock } from "lucide-react";

const PickButton = ({ label, sub, active, onClick, count, testid }) => (
  <button
    onClick={onClick}
    data-testid={testid}
    className={`flex-1 flex flex-col items-center justify-center py-3 rounded-lg border transition-colors duration-200 ${
      active
        ? "bg-[#D92525] border-[#D92525] text-white shadow-sm"
        : "bg-white border-slate-200 text-slate-800 hover:border-[#FCA5A5] hover:bg-[#FEF2F2]"
    }`}
  >
    <span className="font-black text-lg leading-none" style={{ fontFamily: "Outfit, sans-serif" }}>{label}</span>
    <span className={`text-[10px] font-semibold uppercase tracking-wider mt-1 ${active ? "text-red-100" : "text-slate-500"}`}>{sub}</span>
    <span className={`text-[11px] font-mono mt-0.5 ${active ? "text-white" : "text-slate-500"}`}>{count}</span>
  </button>
);

export const DuelCard = ({ duel, myPick, onTipped }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [pick, setPick] = useState(myPick || null);
  const [saving, setSaving] = useState(false);

  const tc = duel.tip_counts || { "1": 0, X: 0, "2": 0 };

  const handlePick = async (choice) => {
    if (!user) {
      toast.error("Du må logge inn for å tippe");
      navigate("/login");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/duels/${duel.id}/tip`, { pick: choice });
      setPick(choice);
      toast.success("Tips lagret!");
      onTipped && onTipped();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-[#FCA5A5] transition-colors duration-200" data-testid={`duel-card-${duel.id}`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#B91C1C] bg-[#FEF2F2] px-2.5 py-1 rounded-full">
          {duel.discipline}
        </span>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse" />
          <span className="text-xs font-semibold text-slate-500">Åpen for tipping</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex-1 text-center">
          <div className="w-11 h-11 mx-auto rounded-full bg-[#D92525] text-white flex items-center justify-center font-black text-lg mb-1" style={{ fontFamily: "Outfit, sans-serif" }}>1</div>
          <p className="font-bold text-slate-900 text-sm leading-tight">{duel.shooter1}</p>
        </div>
        <div className="text-slate-300 font-black text-sm" style={{ fontFamily: "Outfit, sans-serif" }}>VS</div>
        <div className="flex-1 text-center">
          <div className="w-11 h-11 mx-auto rounded-full bg-[#0F172A] text-white flex items-center justify-center font-black text-lg mb-1" style={{ fontFamily: "Outfit, sans-serif" }}>2</div>
          <p className="font-bold text-slate-900 text-sm leading-tight">{duel.shooter2}</p>
        </div>
      </div>

      {(duel.venue || duel.start_time) && (
        <div className="flex items-center justify-center gap-4 text-xs text-slate-500 mb-4">
          {duel.venue && <span className="flex items-center gap-1"><MapPin size={12} /> {duel.venue}</span>}
          {duel.start_time && <span className="flex items-center gap-1"><Clock size={12} /> {duel.start_time}</span>}
        </div>
      )}

      <div className="flex gap-2">
        <PickButton label="1" sub={duel.shooter1.split(" ")[0]} count={`${tc["1"]} tips`} active={pick === "1"} onClick={() => handlePick("1")} testid={`tip-1-${duel.id}`} />
        <PickButton label="U" sub="Uavgjort" count={`${tc["X"]} tips`} active={pick === "X"} onClick={() => handlePick("X")} testid={`tip-X-${duel.id}`} />
        <PickButton label="2" sub={duel.shooter2.split(" ")[0]} count={`${tc["2"]} tips`} active={pick === "2"} onClick={() => handlePick("2")} testid={`tip-2-${duel.id}`} />
      </div>
      {pick && <p className="text-center text-xs text-[#16A34A] font-semibold mt-3" data-testid={`my-pick-${duel.id}`}>Ditt tips er registrert{saving ? "..." : ""}</p>}
    </div>
  );
};
