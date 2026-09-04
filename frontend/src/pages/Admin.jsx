import { useEffect, useState, useCallback } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Shield, Plus, Trash2, Flag } from "lucide-react";

const DISCIPLINES = ["10m Luftrifle", "50m Match", "300m Standardrifle", "Biathlon Sprint", "Felthurtig"];

export default function Admin() {
  const { user } = useAuth();
  const [duels, setDuels] = useState([]);
  const [form, setForm] = useState({ shooter1: "", shooter2: "", shooter1_img: "", shooter2_img: "", discipline: DISCIPLINES[0], venue: "", start_time: "" });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const { data } = await api.get("/duels");
    setDuels(data);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (user === null) return null;
  if (!user || user.role !== "admin") return <Navigate to="/" replace />;

  const createDuel = async (e) => {
    e.preventDefault();
    if (!form.shooter1 || !form.shooter2) return;
    setBusy(true);
    try {
      await api.post("/duels", form);
      toast.success("Duell opprettet!");
      setForm({ shooter1: "", shooter2: "", shooter1_img: "", shooter2_img: "", discipline: DISCIPLINES[0], venue: "", start_time: "" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy(false);
    }
  };

  const removeDuel = async (id) => {
    await api.delete(`/duels/${id}`);
    toast.success("Duell slettet");
    load();
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <Shield size={22} className="text-[#D92525]" />
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Admin-panel</h1>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Create form */}
        <form onSubmit={createDuel} className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 space-y-4 h-fit" data-testid="create-duel-form">
          <h2 className="font-bold text-slate-900 flex items-center gap-2"><Plus size={18} className="text-[#D92525]" /> Ny duell</h2>
          <div>
            <label className="text-sm font-semibold text-slate-700">Skytter 1</label>
            <input data-testid="duel-shooter1" required value={form.shooter1} onChange={(e) => setForm({ ...form, shooter1: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            <input data-testid="duel-shooter1-img" value={form.shooter1_img} onChange={(e) => setForm({ ...form, shooter1_img: e.target.value })} placeholder="Bilde-URL (fra LSres) – valgfritt"
              className="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-[#D92525]" />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Skytter 2</label>
            <input data-testid="duel-shooter2" required value={form.shooter2} onChange={(e) => setForm({ ...form, shooter2: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            <input data-testid="duel-shooter2-img" value={form.shooter2_img} onChange={(e) => setForm({ ...form, shooter2_img: e.target.value })} placeholder="Bilde-URL (fra LSres) – valgfritt"
              className="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-[#D92525]" />
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Disiplin</label>
            <select data-testid="duel-discipline" value={form.discipline} onChange={(e) => setForm({ ...form, discipline: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:border-[#D92525]">
              {DISCIPLINES.map((d) => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-semibold text-slate-700">Sted</label>
              <input data-testid="duel-venue" value={form.venue} onChange={(e) => setForm({ ...form, venue: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">Tidspunkt</label>
              <input data-testid="duel-time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} placeholder="f.eks. 18:00"
                className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            </div>
          </div>
          <button data-testid="submit-duel" disabled={busy} className="w-full py-2.5 bg-[#D92525] hover:bg-[#B91C1C] text-white font-bold rounded-lg transition-colors disabled:opacity-60">
            {busy ? "Oppretter..." : "Opprett duell"}
          </button>
        </form>

        {/* Duel list with result entry */}
        <div className="lg:col-span-3 space-y-3">
          <h2 className="font-bold text-slate-900">Alle dueller ({duels.length})</h2>
          {duels.length === 0 && <p className="text-slate-500 text-sm">Ingen dueller opprettet ennå.</p>}
          {duels.map((d) => (
            <AdminDuelRow key={d.id} duel={d} onChanged={load} onRemove={() => removeDuel(d.id)} />
          ))}
        </div>
      </div>
    </div>
  );
}

function AdminDuelRow({ duel, onChanged, onRemove }) {
  const [outcome, setOutcome] = useState(duel.outcome || "");
  const [score1, setScore1] = useState(duel.score1 || "");
  const [score2, setScore2] = useState(duel.score2 || "");
  const [busy, setBusy] = useState(false);

  const save = async () => {
    if (!outcome) { toast.error("Velg et resultat"); return; }
    setBusy(true);
    try {
      await api.post(`/duels/${duel.id}/result`, { outcome, score1, score2 });
      toast.success("Resultat registrert – poeng delt ut!");
      onChanged();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4" data-testid={`admin-duel-${duel.id}`}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <span className="text-xs text-[#B91C1C] font-semibold uppercase tracking-wider">{duel.discipline}</span>
          <p className="font-bold text-slate-900">{duel.shooter1} <span className="text-slate-400">vs</span> {duel.shooter2}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${duel.status === "finished" ? "bg-slate-100 text-slate-600" : "bg-green-50 text-[#16A34A]"}`}>
            {duel.status === "finished" ? "Avsluttet" : "Åpen"}
          </span>
          <button onClick={onRemove} data-testid={`delete-duel-${duel.id}`} className="p-1.5 text-slate-400 hover:text-[#D92525] hover:bg-[#FEF2F2] rounded-md transition-colors">
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-2">
        <div className="flex gap-1">
          {[["1", "1"], ["X", "U"], ["2", "2"]].map(([val, lbl]) => (
            <button key={val} onClick={() => setOutcome(val)} data-testid={`result-${val}-${duel.id}`}
              className={`w-9 h-9 rounded-lg font-black text-sm transition-colors ${outcome === val ? "bg-[#D92525] text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
              style={{ fontFamily: "Outfit, sans-serif" }}>
              {lbl}
            </button>
          ))}
        </div>
        <input value={score1} onChange={(e) => setScore1(e.target.value)} placeholder="Score 1" data-testid={`score1-${duel.id}`}
          className="w-20 px-2 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:border-[#D92525]" />
        <input value={score2} onChange={(e) => setScore2(e.target.value)} placeholder="Score 2" data-testid={`score2-${duel.id}`}
          className="w-20 px-2 py-2 border border-slate-200 rounded-lg text-sm font-mono focus:outline-none focus:border-[#D92525]" />
        <button onClick={save} disabled={busy} data-testid={`save-result-${duel.id}`}
          className="flex items-center gap-1.5 px-3 py-2 bg-[#0F172A] hover:bg-slate-800 text-white text-sm font-bold rounded-lg transition-colors disabled:opacity-60">
          <Flag size={14} /> {duel.status === "finished" ? "Oppdater" : "Registrer"}
        </button>
      </div>
    </div>
  );
}
