import { useEffect, useState, useCallback } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Shield, Plus, Trash2, Flag, Trophy, Image as ImageIcon, Users, Crown } from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";

const DISCIPLINES = ["100m", "200m", "300m", "15m", "50m", "Feltskyting", "Stangskyting", "Felthurtigskyting"];

export default function Admin() {
  const { user } = useAuth();
  const [duels, setDuels] = useState([]);
  const [tournaments, setTournaments] = useState([]);
  const [users, setUsers] = useState([]);
  const [heroInput, setHeroInput] = useState("");
  const [form, setForm] = useState({ shooter1: "", shooter2: "", shooter1_img: "", shooter2_img: "", discipline: DISCIPLINES[0], venue: "", start_time: "", start_at: "", tournament_id: "" });
  const [seasonForm, setSeasonForm] = useState({ name: "", season: "" });
  const [duelTab, setDuelTab] = useState("active");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [d, t, s, u] = await Promise.all([
      api.get("/duels"), api.get("/tournaments"), api.get("/settings"), api.get("/admin/users"),
    ]);
    setDuels(d.data);
    setTournaments(t.data);
    setHeroInput(s.data.hero_image || "");
    setUsers(u.data);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (user === null) return null;
  if (!user || user.role !== "admin") return <Navigate to="/" replace />;

  const activeDuels = duels.filter((d) => d.status !== "finished");
  const finishedDuels = duels.filter((d) => d.status === "finished");
  const shownDuels = duelTab === "active" ? activeDuels : finishedDuels;

  const saveHero = async (e) => {
    e.preventDefault();
    try {
      await api.put("/settings", { hero_image: heroInput });
      toast.success("Bakgrunnsbilde oppdatert!");
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const setRole = async (id, role) => {
    try {
      await api.post(`/admin/users/${id}/role`, { role });
      toast.success(role === "admin" ? "Bruker gjort til admin" : "Admin-rolle fjernet");
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const createDuel = async (e) => {
    e.preventDefault();
    if (!form.shooter1 || !form.shooter2) return;
    setBusy(true);
    try {
      await api.post("/duels", form);
      toast.success("Duell opprettet!");
      setForm({ shooter1: "", shooter2: "", shooter1_img: "", shooter2_img: "", discipline: DISCIPLINES[0], venue: "", start_time: "", start_at: "", tournament_id: "" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy(false);
    }
  };

  const createSeason = async (e) => {
    e.preventDefault();
    if (!seasonForm.name) return;
    try {
      await api.post("/tournaments", seasonForm);
      toast.success("Sesong opprettet!");
      setSeasonForm({ name: "", season: "" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const removeSeason = async (id) => {
    await api.delete(`/tournaments/${id}`);
    toast.success("Sesong slettet");
    load();
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
            <div className="mt-2">
              <ImageUpload value={form.shooter1_img} onChange={(url) => setForm({ ...form, shooter1_img: url })} testid="duel-shooter1-img" label="Last opp bilde av skytter 1" />
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Skytter 2</label>
            <input data-testid="duel-shooter2" required value={form.shooter2} onChange={(e) => setForm({ ...form, shooter2: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            <div className="mt-2">
              <ImageUpload value={form.shooter2_img} onChange={(url) => setForm({ ...form, shooter2_img: url })} testid="duel-shooter2-img" label="Last opp bilde av skytter 2" />
            </div>
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
              <label className="text-sm font-semibold text-slate-700">Starttidspunkt</label>
              <input data-testid="duel-startat" type="datetime-local" value={form.start_at} onChange={(e) => setForm({ ...form, start_at: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Serie / Sesong</label>
            <select data-testid="duel-tournament" value={form.tournament_id} onChange={(e) => setForm({ ...form, tournament_id: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:border-[#D92525]">
              <option value="">Ingen serie</option>
              {tournaments.map((t) => <option key={t.id} value={t.id}>{t.name}{t.season ? ` (${t.season})` : ""}</option>)}
            </select>
          </div>
          <button data-testid="submit-duel" disabled={busy} className="w-full py-2.5 bg-[#D92525] hover:bg-[#B91C1C] text-white font-bold rounded-lg transition-colors disabled:opacity-60">
            {busy ? "Oppretter..." : "Opprett duell"}
          </button>
        </form>

        {/* Duel list with result entry */}
        <div className="lg:col-span-3 space-y-3">
          {/* Season management */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 className="font-bold text-slate-900 flex items-center gap-2 mb-4"><Trophy size={18} className="text-[#EAB308]" /> Serier / Sesonger</h2>
            <form onSubmit={createSeason} className="flex flex-col sm:flex-row gap-2 mb-4" data-testid="create-season-form">
              <input data-testid="season-name" required value={seasonForm.name} onChange={(e) => setSeasonForm({ ...seasonForm, name: e.target.value })} placeholder="Navn (f.eks. Vintercupen)"
                className="flex-1 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
              <input data-testid="season-period" value={seasonForm.season} onChange={(e) => setSeasonForm({ ...seasonForm, season: e.target.value })} placeholder="Sesong (f.eks. 2026)"
                className="w-full sm:w-40 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
              <button data-testid="submit-season" className="px-4 py-2 bg-[#0F172A] hover:bg-slate-800 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5">
                <Plus size={16} /> Legg til
              </button>
            </form>
            {tournaments.length === 0 ? (
              <p className="text-slate-500 text-sm">Ingen serier ennå.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tournaments.map((t) => (
                  <span key={t.id} className="flex items-center gap-2 bg-slate-100 rounded-full pl-3 pr-1.5 py-1 text-sm font-semibold text-slate-700" data-testid={`admin-season-${t.id}`}>
                    {t.name}{t.season ? ` · ${t.season}` : ""} <span className="text-xs text-slate-400">({t.duel_count})</span>
                    <button onClick={() => removeSeason(t.id)} data-testid={`delete-season-${t.id}`} className="p-1 text-slate-400 hover:text-[#D92525] rounded-full"><Trash2 size={13} /></button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 pt-2">
            <button onClick={() => setDuelTab("active")} data-testid="admin-tab-active"
              className={`px-3 py-1.5 rounded-full text-sm font-semibold transition-colors ${duelTab === "active" ? "bg-[#D92525] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
              Aktive ({activeDuels.length})
            </button>
            <button onClick={() => setDuelTab("finished")} data-testid="admin-tab-finished"
              className={`px-3 py-1.5 rounded-full text-sm font-semibold transition-colors ${duelTab === "finished" ? "bg-[#D92525] text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>
              Avsluttede ({finishedDuels.length})
            </button>
          </div>
          {shownDuels.length === 0 && (
            <p className="text-slate-500 text-sm" data-testid="admin-duels-empty">
              {duelTab === "active" ? "Ingen aktive dueller." : "Ingen avsluttede dueller ennå."}
            </p>
          )}
          {shownDuels.map((d) => (
            <AdminDuelRow key={d.id} duel={d} onChanged={load} onRemove={() => removeDuel(d.id)} />
          ))}

          {/* Hero background */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 mt-4" data-testid="hero-settings">
            <h2 className="font-bold text-slate-900 flex items-center gap-2 mb-4"><ImageIcon size={18} className="text-[#D92525]" /> Bakgrunnsbilde (forside)</h2>
            {heroInput && <img src={heroInput} alt="Forhåndsvisning" className="w-full h-32 object-cover rounded-lg border border-slate-200 mb-3" />}
            <form onSubmit={saveHero} className="flex flex-col sm:flex-row gap-2">
              <input data-testid="hero-url" value={heroInput} onChange={(e) => setHeroInput(e.target.value)} placeholder="Bilde-URL"
                className="flex-1 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
              <button data-testid="save-hero" className="px-4 py-2 bg-[#0F172A] hover:bg-slate-800 text-white font-bold rounded-lg transition-colors">Lagre</button>
            </form>
            <p className="text-xs text-slate-400 mt-2">Endres når som helst – også etter at siden er publisert.</p>
          </div>

          {/* User management */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 mt-4" data-testid="user-management">
            <h2 className="font-bold text-slate-900 flex items-center gap-2 mb-4"><Users size={18} className="text-[#D92525]" /> Brukere ({users.length})</h2>
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between gap-3 py-2 border-b border-slate-100 last:border-0" data-testid={`user-row-${u.id}`}>
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-900 text-sm truncate flex items-center gap-1.5">
                      {u.role === "admin" && <Crown size={13} className="text-[#EAB308] shrink-0" />}
                      {u.name}
                    </p>
                    <p className="text-xs text-slate-400 truncate">{u.email}</p>
                  </div>
                  {u.is_seed_admin ? (
                    <span className="text-xs font-semibold text-slate-400 shrink-0">Hovedadmin</span>
                  ) : u.role === "admin" ? (
                    <button onClick={() => setRole(u.id, "user")} data-testid={`demote-${u.id}`} className="text-xs font-semibold text-slate-600 hover:text-[#D92525] border border-slate-200 rounded-full px-3 py-1.5 transition-colors shrink-0">Fjern admin</button>
                  ) : (
                    <button onClick={() => setRole(u.id, "admin")} data-testid={`promote-${u.id}`} className="text-xs font-bold text-white bg-[#D92525] hover:bg-[#B91C1C] rounded-full px-3 py-1.5 transition-colors shrink-0">Gjør til admin</button>
                  )}
                </div>
              ))}
            </div>
          </div>
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

  const saveImage = async (field, url) => {
    try {
      await api.patch(`/duels/${duel.id}`, { [field]: url });
      onChanged();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
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

      <div className="grid sm:grid-cols-2 gap-3 mt-4 pt-3 border-t border-slate-100">
        <div>
          <p className="text-xs font-semibold text-slate-500 mb-1">Bilde: {duel.shooter1}</p>
          <ImageUpload value={duel.shooter1_img} onChange={(url) => saveImage("shooter1_img", url)} testid={`edit-img1-${duel.id}`} label="Last opp / bytt" />
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-500 mb-1">Bilde: {duel.shooter2}</p>
          <ImageUpload value={duel.shooter2_img} onChange={(url) => saveImage("shooter2_img", url)} testid={`edit-img2-${duel.id}`} label="Last opp / bytt" />
        </div>
      </div>
    </div>
  );
}
