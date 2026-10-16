import { useEffect, useState, useCallback, useMemo } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Shield, Plus, Trash2, Flag, Trophy, Image as ImageIcon, Users, Crown, RefreshCw, ExternalLink, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { ImageUpload } from "@/components/ImageUpload";

const DISCIPLINES = ["100m", "200m", "300m", "15m", "50m", "Feltskyting", "Stangskyting", "Felthurtigskyting"];
const EXTERNAL_SOURCES = [
  { value: "", label: "Ingen" },
  { value: "mittdfs", label: "MittDFS" },
  { value: "megalink", label: "Megalink" },
];

export default function Admin() {
  const { user } = useAuth();
  const [duels, setDuels] = useState([]);
  const [tournaments, setTournaments] = useState([]);
  const [users, setUsers] = useState([]);
  const [heroInput, setHeroInput] = useState("");
  const [form, setForm] = useState({
shooter1: "",
shooter2: "",
shooter1_club: "",
shooter2_club: "",
shooter1_class: "",
shooter2_class: "",
shooter1_img: "",
shooter2_img: "",
  discipline: DISCIPLINES[0],
  venue: "",
  start_time: "",
  start_at: "",
  tournament_ids: [],
  external_source: "",
  external_event_url: "",
  external_event_id: "",
  external_discipline_id: "",
  external_class_id: "",
});
  const [seasonForm, setSeasonForm] = useState({ name: "", season: "", is_private: false, access_code: "" });
  const [duelTab, setDuelTab] = useState("active");
  const [busy, setBusy] = useState(false);
  const [suggestions, setSuggestions] = useState({ counts: { waiting: 0, suggested: 0, approved: 0, rejected: 0, needs_review: 0 }, items: [] });
  const [suggestionFilter, setSuggestionFilter] = useState("waiting,suggested,needs_review");
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [suggestionBusy, setSuggestionBusy] = useState(false);
  const [rejectionNote, setRejectionNote] = useState("");
  const [editSuggestion, setEditSuggestion] = useState({ outcome: "", score1: "", score2: "" });
  const [participantText, setParticipantText] = useState("");
  const [participantSearch, setParticipantSearch] = useState("");

  const load = useCallback(async () => {
const d = await api.get("/duels");

const t = await api.get("/tournaments").catch(() => ({ data: [] }));
const s = await api.get("/settings").catch(() => ({ data: {} }));
const u = await api.get("/admin/users").catch(() => ({ data: [] }));
    setDuels(d.data);
    setTournaments(t.data);
    setHeroInput(s.data.hero_image || "");
    setUsers(u.data);
  }, []);

  const loadSuggestions = useCallback(async (statusValue = suggestionFilter) => {
    try {
      const resp = await api.get("/admin/result-suggestions", {
        params: { status: statusValue },
      });
      setSuggestions(resp.data || { counts: {}, items: [] });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    }
  }, [suggestionFilter]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { loadSuggestions(); }, [loadSuggestions]);

  if (user === null) return null;
  if (!user || user.role !== "admin") return <Navigate to="/" replace />;

  const activeDuels = duels.filter((d) => d.status !== "finished");
  const finishedDuels = duels.filter((d) => d.status === "finished");
  const shownDuels = duelTab === "active" ? activeDuels : finishedDuels;
  const importReadyDuels = duels.filter((d) => d.external_source && d.external_event_url);
  const participants = useMemo(() => {
  const names = participantText
    .split(/\r?\n/)
    .map((name) => name.trim())
    .filter(Boolean);

  const uniqueNames = [...new Set(names)];

  if (!participantSearch.trim()) {
    return uniqueNames;
  }

  const search = participantSearch.toLowerCase();

  return uniqueNames.filter((name) =>
    name.toLowerCase().includes(search)
  );
  }, [participantText, participantSearch]);

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
  const removeUser = async (id, name) => {
  if (!window.confirm(`Er du sikker på at du vil slette brukeren ${name}?`)) {
    return;
  }

  try {
    await api.delete(`/admin/users/${id}`);
    toast.success("Brukeren er slettet");
    load();
  } catch (err) {
    toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
  }
};

  const createDuel = async (e) => {
    e.preventDefault();
  if (!form.shooter1 || !form.shooter2) {
  toast.error("Velg to skyttere før du oppretter duellen.");
  return;
}

  if (form.shooter1 === form.shooter2) {
  toast.error("Skytter 1 og Skytter 2 må være forskjellige.");
  return;
}
    setBusy(true);
    try {
      await api.post("/duels", form);
      toast.success("Duell opprettet!");
      setForm({
shooter1: "",
shooter2: "",
shooter1_club: "",
shooter2_club: "",
shooter1_class: "",
shooter2_class: "",
shooter1_img: "",
shooter2_img: "",
  discipline: DISCIPLINES[0],
  venue: "",
  start_time: "",
  start_at: "",
  tournament_ids: [],
  external_source: "",
  external_event_url: "",
  external_event_id: "",
  external_discipline_id: "",
  external_class_id: "",
});
      load();
      loadSuggestions();
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
      setSeasonForm({ name: "", season: "", is_private: false, access_code: "" });
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

    const resetSeasonPoints = async (id) => {
    if (!window.confirm("Nullstille poengene i denne konkurransen?")) {
      return;
    }

    try {
      await api.post(`/tournaments/${id}/reset-points`);
      toast.success("Poengene i konkurransen er nullstilt");
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    }
  };
  const resetGlobalPoints = async () => {
    if (!window.confirm("Nullstille totalpoengene for alle brukere?")) {
      return;
    }

    try {
      await api.post("/leaderboard/reset-points");
      toast.success("Totalpoengene er nullstilt");
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    }
  };
  const resetPointsForSeason = async (season) => {
    if (!season) return;

    if (!window.confirm(`Nullstille poengene for hele sesongen ${season}?`)) {
      return;
    }

    try {
      await api.post(`/seasons/${encodeURIComponent(season)}/reset-points`);
      toast.success(`Poengene for sesongen ${season} er nullstilt`);
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    }
  };
  const removeDuel = async (id) => {
    await api.delete(`/duels/${id}`);
    toast.success("Duell slettet");
    load();
    loadSuggestions();
  };

  const openSuggestion = async (suggestionId) => {
    try {
      const response = await api.get(`/admin/result-suggestions/${suggestionId}`);
      const details = response.data;
      setSelectedSuggestion(details);
      setRejectionNote(details.rejection_note || "");
      setEditSuggestion({
        outcome: details.suggested_outcome || "",
        score1: details.suggested_score1 || "",
        score2: details.suggested_score2 || "",
      });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    }
  };

  const refreshSuggestionForDuel = async (duelId) => {
    setSuggestionBusy(true);
    try {
      const response = await api.post(`/admin/duels/${duelId}/result-suggestions/fetch`);
      toast.success(response.data?.message || "Resultatforslag oppdatert");
      await loadSuggestions();
      await openSuggestion(response.data.id);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    } finally {
      setSuggestionBusy(false);
    }
  };

  const approveSuggestion = async () => {
    if (!selectedSuggestion) return;
    if (!window.confirm("Godkjenne dette resultatet og oppdatere duellen?")) return;

    setSuggestionBusy(true);
    try {
      await api.post(
        `/admin/duels/${selectedSuggestion.duel_id}/result-suggestions/${selectedSuggestion.id}/approve`,
        editSuggestion
      );
      toast.success("Resultatet er godkjent og registrert");
      await load();
      await loadSuggestions();
      await openSuggestion(selectedSuggestion.id);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    } finally {
      setSuggestionBusy(false);
    }
  };

  const rejectSuggestion = async () => {
    if (!selectedSuggestion) return;
    setSuggestionBusy(true);
    try {
      await api.post(
        `/admin/duels/${selectedSuggestion.duel_id}/result-suggestions/${selectedSuggestion.id}/reject`,
        { note: rejectionNote }
      );
      toast.success("Forslaget er avvist");
      await loadSuggestions();
      await openSuggestion(selectedSuggestion.id);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    } finally {
      setSuggestionBusy(false);
    }
  };

  const filterSuggestions = async (value) => {
    setSuggestionFilter(value);
    await loadSuggestions(value);
  };

  const statusBadge = (status) => {
    if (status === "approved") return "bg-emerald-100 text-emerald-700";
    if (status === "rejected") return "bg-rose-100 text-rose-700";
    if (status === "suggested") return "bg-blue-100 text-blue-700";
    if (status === "needs_review") return "bg-amber-100 text-amber-800";
    return "bg-slate-100 text-slate-700";
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <Shield size={22} className="text-[#D92525]" />
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Admin-panel</h1>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
         {/* Choose participants */}
<form
  onSubmit={createDuel}
  className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 space-y-4 h-fit"
  data-testid="create-duel-form"
>
<h2 className="font-bold text-slate-900 flex items-center gap-2">
  <Plus size={18} className="text-[#D92525]" />
  Ny duell
</h2>

<div>
  <label className="text-sm font-semibold text-slate-700">
    Skytter 1
  </label>
            <input data-testid="duel-shooter1" required value={form.shooter1} onChange={(e) => setForm({ ...form, shooter1: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            <input
  value={form.shooter1_club}
  onChange={(e) => setForm({ ...form, shooter1_club: e.target.value })}
  placeholder="Skytterlag"
  className="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
/>
            <input
  value={form.shooter1_class}
  onChange={(e) => setForm({ ...form, shooter1_class: e.target.value })}
  placeholder="Klasse"
  className="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
/>
            <div className="mt-2">
              <ImageUpload value={form.shooter1_img} onChange={(url) => setForm({ ...form, shooter1_img: url })} testid="duel-shooter1-img" label="Last opp bilde av skytter 1" />
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Skytter 2</label>
            <input data-testid="duel-shooter2" required value={form.shooter2} onChange={(e) => setForm({ ...form, shooter2: e.target.value })}
              className="mt-1 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
            <input
  value={form.shooter2_club}
  onChange={(e) => setForm({ ...form, shooter2_club: e.target.value })}
  placeholder="Skytterlag"
  className="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
/>
            <input
  value={form.shooter2_class}
  onChange={(e) => setForm({ ...form, shooter2_class: e.target.value })}
  placeholder="Klasse"
  className="mt-2 w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
/>
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
          <div className="border border-slate-200 rounded-xl p-3 space-y-2">
            <p className="text-sm font-semibold text-slate-700">Ekstern resultatkobling</p>
            <select
              value={form.external_source}
              onChange={(e) => setForm({ ...form, external_source: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:border-[#D92525]"
            >
              {EXTERNAL_SOURCES.map((source) => (
                <option key={source.value} value={source.value}>{source.label}</option>
              ))}
            </select>
            <input
              value={form.external_event_url}
              onChange={(e) => setForm({ ...form, external_event_url: e.target.value })}
              placeholder="Resultat-URL (https://...)"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
            />
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <input
                value={form.external_event_id}
                onChange={(e) => setForm({ ...form, external_event_id: e.target.value })}
                placeholder="Event-ID (valgfri)"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
              />
              <input
                value={form.external_discipline_id}
                onChange={(e) => setForm({ ...form, external_discipline_id: e.target.value })}
                placeholder="Øvelse-ID (valgfri)"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
              />
              <input
                value={form.external_class_id}
                onChange={(e) => setForm({ ...form, external_class_id: e.target.value })}
                placeholder="Klasse-ID (valgfri)"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-semibold text-slate-700">Konkurranser / Sesonger</label>

<div className="mt-2 space-y-2">
  {tournaments.map((t) => (
    <label key={t.id} className="flex items-center gap-2 text-sm text-slate-700">
      <input
        type="checkbox"
        checked={form.tournament_ids.includes(t.id)}
        onChange={(e) => {
          const tournament_ids = e.target.checked
            ? [...form.tournament_ids, t.id]
            : form.tournament_ids.filter((id) => id !== t.id);

          setForm({ ...form, tournament_ids });
        }}
      />
      {t.name}{t.season ? ` (${t.season})` : ""}
    </label>
  ))}

  {tournaments.length === 0 && (
    <p className="text-sm text-slate-400">Ingen konkurranser opprettet.</p>
  )}
</div>
            
          </div>
          <button data-testid="submit-duel" disabled={busy} className="w-full py-2.5 bg-[#D92525] hover:bg-[#B91C1C] text-white font-bold rounded-lg transition-colors disabled:opacity-60">
            {busy ? "Oppretter..." : "Opprett duell"}
          </button>
        </form>

        {/* Duel list with result entry */}
        <div className="lg:col-span-3 space-y-3">
          {/* Season management */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 className="font-bold text-slate-900 flex items-center gap-2 mb-4"><Trophy size={18} className="text-[#EAB308]" /> Konkurranser / Sesonger</h2>
            <form onSubmit={createSeason} className="flex flex-col sm:flex-row gap-2 mb-4" data-testid="create-season-form">
              <input data-testid="season-name" required value={seasonForm.name} onChange={(e) => setSeasonForm({ ...seasonForm, name: e.target.value })} placeholder="Navn (f.eks. Vintercupen)"
                className="flex-1 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
              <input data-testid="season-period" value={seasonForm.season} onChange={(e) => setSeasonForm({ ...seasonForm, season: e.target.value })} placeholder="Sesong (f.eks. 2026)"
                className="w-full sm:w-40 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]" />
              <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 px-2">
  <input
    type="checkbox"
    checked={seasonForm.is_private}
    onChange={(e) => setSeasonForm({ ...seasonForm, is_private: e.target.checked })}
  />
  Privat konkurranse
</label>
              {seasonForm.is_private && (
  <input
    value={seasonForm.access_code}
    onChange={(e) => setSeasonForm({ ...seasonForm, access_code: e.target.value })}
    placeholder="Kode til privat konkurranse"
    className="w-full sm:w-48 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-[#D92525]"
  />
)}
              <button data-testid="submit-season" className="px-4 py-2 bg-[#0F172A] hover:bg-slate-800 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-1.5">
                <Plus size={16} /> Legg til
              </button>
            </form>
            <button
  type="button"
  onClick={resetGlobalPoints}
  className="mb-4 px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-bold rounded-lg transition-colors"
>
  Nullstill totalpoeng
</button>
            {tournaments.length === 0 ? (
              <p className="text-slate-500 text-sm">Ingen konkurranser ennå.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tournaments.map((t) => (
                  <span key={t.id} className="flex items-center gap-2 bg-slate-100 rounded-full pl-3 pr-1.5 py-1 text-sm font-semibold text-slate-700" data-testid={`admin-season-${t.id}`}>
                    {t.name}{t.season ? ` · ${t.season}` : ""}{t.is_private ? " 🔒" : ""} <span className="text-xs text-slate-400">({t.duel_count})</span>
                    <button
  type="button"
  onClick={() => resetSeasonPoints(t.id)}
  className="px-2 py-1 text-xs font-bold text-slate-600 hover:text-[#D92525] border border-slate-200 rounded-full"
>
  Nullstill poeng
</button>
                    {t.season && (
  <button
    type="button"
    onClick={() => resetPointsForSeason(t.season)}
    className="px-2 py-1 text-xs font-bold text-slate-600 hover:text-[#D92525] border border-slate-200 rounded-full"
  >
    Nullstill sesong
  </button>
)}
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

          <div className="bg-white border border-slate-200 rounded-2xl p-6 mt-4 space-y-4" data-testid="result-import">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <RefreshCw size={18} className="text-[#D92525]" /> Resultatimport
              </h2>
              <button
                type="button"
                disabled={suggestionBusy}
                onClick={() => loadSuggestions()}
                className="px-3 py-1.5 text-xs font-bold border border-slate-200 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-60"
              >
                Oppdater liste
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
              {Object.entries(suggestions.counts || {}).map(([key, value]) => (
                <div key={key} className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-2">
                  <p className="uppercase text-slate-500">{key}</p>
                  <p className="font-bold text-slate-900">{value}</p>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={suggestionFilter}
                onChange={(e) => filterSuggestions(e.target.value)}
                className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                <option value="waiting,suggested,needs_review">Venter / foreslått / må sjekkes</option>
                <option value="suggested">Kun foreslått</option>
                <option value="needs_review">Kun needs_review</option>
                <option value="approved,rejected">Behandlede</option>
              </select>
              <span className="text-xs text-slate-500">
                Relevante dueller: {importReadyDuels.length}
              </span>
            </div>

            {importReadyDuels.length === 0 ? (
              <p className="text-sm text-slate-500">
                Ingen dueller er koblet til ekstern kilde ennå.
              </p>
            ) : (
              <div className="space-y-2">
                {importReadyDuels.slice(0, 8).map((duel) => (
                  <div key={`import-duel-${duel.id}`} className="flex items-center justify-between gap-2 border border-slate-100 rounded-lg px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-900 truncate">
                        #{duel.id} {duel.shooter1} vs {duel.shooter2}
                      </p>
                      <p className="text-xs text-slate-500 truncate">
                        {duel.external_source?.toUpperCase()} · {duel.external_event_url}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => refreshSuggestionForDuel(duel.id)}
                      disabled={suggestionBusy}
                      className="px-3 py-1.5 text-xs font-bold bg-slate-100 hover:bg-slate-200 rounded-lg disabled:opacity-60"
                    >
                      Hent forslag
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                {(suggestions.items || []).length === 0 ? (
                  <p className="text-sm text-slate-500">Ingen forslag i valgt filter.</p>
                ) : (
                  (suggestions.items || []).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => openSuggestion(item.id)}
                      className="w-full text-left border border-slate-200 rounded-lg p-3 hover:bg-slate-50"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-slate-900">
                          Duell #{item.duel_id}
                        </p>
                        <span className={`text-[11px] font-bold px-2 py-1 rounded-full ${statusBadge(item.status)}`}>
                          {item.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">
                        {item.suggested_shooter1_name || item.duel?.shooter1} {item.suggested_score1 || "-"} - {item.suggested_score2 || "-"} {item.suggested_shooter2_name || item.duel?.shooter2}
                      </p>
                    </button>
                  ))
                )}
              </div>

              <div className="border border-slate-200 rounded-xl p-4">
                {!selectedSuggestion ? (
                  <p className="text-sm text-slate-500">Velg et forslag for detaljer.</p>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-bold text-slate-900">
                        Forslag #{selectedSuggestion.id} (duell #{selectedSuggestion.duel_id})
                      </p>
                      <span className={`text-[11px] font-bold px-2 py-1 rounded-full ${statusBadge(selectedSuggestion.status)}`}>
                        {selectedSuggestion.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 space-y-1">
                      <p>Kilde: {selectedSuggestion.source?.toUpperCase() || "-"}</p>
                      <p>Hentet: {selectedSuggestion.fetched_at ? new Date(selectedSuggestion.fetched_at).toLocaleString("nb-NO") : "Ikke hentet"}</p>
                      {selectedSuggestion.status_reason === "source_unavailable" || selectedSuggestion.status_reason === "parser_unavailable" ? (
                        <p className="text-amber-700 flex items-center gap-1"><AlertTriangle size={13} /> Kildefeil eller utilgjengelig parser.</p>
                      ) : null}
                      {selectedSuggestion.status_reason === "ambiguous_match" ? (
                        <p className="text-amber-700 flex items-center gap-1"><AlertTriangle size={13} /> Flere mulige treff.</p>
                      ) : null}
                      {selectedSuggestion.status_reason === "no_result" || selectedSuggestion.status_reason === "missing_event_url" ? (
                        <p className="text-slate-500">Ingen resultat funnet ennå.</p>
                      ) : null}
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                      <input
                        value={editSuggestion.score1}
                        onChange={(e) => setEditSuggestion({ ...editSuggestion, score1: e.target.value })}
                        placeholder="Score 1"
                        className="px-2 py-2 border border-slate-200 rounded-lg text-sm"
                      />
                      <input
                        value={editSuggestion.score2}
                        onChange={(e) => setEditSuggestion({ ...editSuggestion, score2: e.target.value })}
                        placeholder="Score 2"
                        className="px-2 py-2 border border-slate-200 rounded-lg text-sm"
                      />
                      <select
                        value={editSuggestion.outcome}
                        onChange={(e) => setEditSuggestion({ ...editSuggestion, outcome: e.target.value })}
                        className="px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white"
                      >
                        <option value="">Utfall</option>
                        <option value="1">1</option>
                        <option value="X">X</option>
                        <option value="2">2</option>
                      </select>
                    </div>

                    <textarea
                      value={rejectionNote}
                      onChange={(e) => setRejectionNote(e.target.value)}
                      placeholder="Notat ved avvisning (valgfritt)"
                      className="w-full min-h-20 px-2 py-2 border border-slate-200 rounded-lg text-sm"
                    />

                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={approveSuggestion}
                        disabled={suggestionBusy}
                        className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold rounded-lg disabled:opacity-60 flex items-center gap-1"
                      >
                        <CheckCircle2 size={14} /> Godkjenn resultat
                      </button>
                      <button
                        type="button"
                        onClick={rejectSuggestion}
                        disabled={suggestionBusy}
                        className="px-3 py-2 bg-rose-600 hover:bg-rose-700 text-white text-sm font-bold rounded-lg disabled:opacity-60 flex items-center gap-1"
                      >
                        <XCircle size={14} /> Avvis
                      </button>
                      <button
                        type="button"
                        onClick={() => refreshSuggestionForDuel(selectedSuggestion.duel_id)}
                        disabled={suggestionBusy}
                        className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-bold rounded-lg disabled:opacity-60"
                      >
                        Rediger / hent på nytt
                      </button>
                      {selectedSuggestion.event_url && (
                        <a
                          href={selectedSuggestion.event_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-sm font-bold rounded-lg inline-flex items-center gap-1"
                        >
                          <ExternalLink size={14} /> Åpne kilde
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Hero background */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 mt-4" data-testid="hero-settings">
            <h2 className="font-bold text-slate-900 flex items-center gap-2 mb-4"><ImageIcon size={18} className="text-[#D92525]" /> Bakgrunnsbilde (forside)</h2>
            {heroInput && <img src={heroInput} alt="Forhåndsvisning" className="w-full h-32 object-cover rounded-lg border border-slate-200 mb-3" />}
          <form onSubmit={saveHero} className="flex flex-col gap-3">
  <ImageUpload
    value={heroInput}
    onChange={setHeroInput}
    testid="hero-image-upload"
    label="Last opp bakgrunnsbilde"
  />

  <button
    data-testid="save-hero"
    className="px-4 py-2 bg-[#0F172A] hover:bg-slate-800 text-white font-bold rounded-lg transition-colors"
  >
    Lagre
  </button>
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
                      {u.username}
                    </p>
                  </div>
<div className="flex items-center gap-2 shrink-0">
  {u.is_seed_admin ? (
    <span className="text-xs font-semibold text-slate-400">Hovedadmin</span>
  ) : u.role === "admin" ? (
    <button
      onClick={() => setRole(u.id, "user")}
      data-testid={`demote-${u.id}`}
      className="text-xs font-semibold text-slate-600 hover:text-[#D92525] border border-slate-200 rounded-full px-3 py-1.5 transition-colors"
    >
      Fjern admin
    </button>
  ) : (
    <>
      <button
        onClick={() => setRole(u.id, "admin")}
        data-testid={`promote-${u.id}`}
        className="text-xs font-bold text-white bg-[#D92525] hover:bg-[#B91C1C] rounded-full px-3 py-1.5 transition-colors"
      >
        Gjør til admin
      </button>

      <button
        onClick={() => removeUser(u.id, u.name || u.username)}
        data-testid={`delete-user-${u.id}`}
        className="p-1.5 text-slate-400 hover:text-[#D92525] hover:bg-[#FEF2F2] rounded-md transition-colors"
        title="Slett bruker"
      >
        <Trash2 size={16} />
      </button>
    </>
  )}
</div>
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
  const [externalSource, setExternalSource] = useState(duel.external_source || "");
  const [externalEventUrl, setExternalEventUrl] = useState(duel.external_event_url || "");
  const [externalEventId, setExternalEventId] = useState(duel.external_event_id || "");
  const [externalDisciplineId, setExternalDisciplineId] = useState(duel.external_discipline_id || "");
  const [externalClassId, setExternalClassId] = useState(duel.external_class_id || "");
  const [busy, setBusy] = useState(false);
  const isPastDeadline = duel.start_at
  ? new Date() >= new Date(duel.start_at)
  : false;

const statusText =
  duel.status === "finished"
    ? "Avsluttet"
    : isPastDeadline
      ? "Venter på resultat"
      : "Åpen";
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
  const saveExternalLink = async () => {
    try {
      await api.patch(`/duels/${duel.id}`, {
        external_source: externalSource,
        external_event_url: externalEventUrl,
        external_event_id: externalEventId,
        external_discipline_id: externalDisciplineId,
        external_class_id: externalClassId,
      });
      toast.success("Ekstern kobling lagret");
      onChanged();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
    }
  };
  const removePoints = async () => {
  if (!window.confirm("Fjerne poengene fra denne duellen for alle brukere?")) {
    return;
  }

  try {
    await api.post(`/duels/${duel.id}/remove-points`);
    toast.success("Poengene fra duellen er fjernet");
    onChanged();
  } catch (err) {
    toast.error(formatApiError(err.response?.data?.error || err.response?.data?.detail));
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
            {statusText}
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
        {duel.status === "finished" && (
  <button
    onClick={removePoints}
    className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-bold rounded-lg transition-colors"
  >
    Fjern poeng
  </button>
)}
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
      <div className="mt-3 pt-3 border-t border-slate-100 space-y-2">
        <p className="text-xs font-semibold text-slate-500">Ekstern resultatkobling</p>
        <div className="grid sm:grid-cols-5 gap-2">
          <select
            value={externalSource}
            onChange={(e) => setExternalSource(e.target.value)}
            className="px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white"
          >
            {EXTERNAL_SOURCES.map((source) => (
              <option key={source.value} value={source.value}>{source.label}</option>
            ))}
          </select>
          <input
            value={externalEventUrl}
            onChange={(e) => setExternalEventUrl(e.target.value)}
            placeholder="Resultat-URL"
            className="sm:col-span-2 px-2 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <input
            value={externalEventId}
            onChange={(e) => setExternalEventId(e.target.value)}
            placeholder="Event-ID"
            className="px-2 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <button
            type="button"
            onClick={saveExternalLink}
            className="px-3 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-bold rounded-lg"
          >
            Lagre kobling
          </button>
        </div>
        <div className="grid sm:grid-cols-2 gap-2">
          <input
            value={externalDisciplineId}
            onChange={(e) => setExternalDisciplineId(e.target.value)}
            placeholder="Øvelse-ID (valgfri)"
            className="px-2 py-2 border border-slate-200 rounded-lg text-sm"
          />
          <input
            value={externalClassId}
            onChange={(e) => setExternalClassId(e.target.value)}
            placeholder="Klasse-ID (valgfri)"
            className="px-2 py-2 border border-slate-200 rounded-lg text-sm"
          />
        </div>
      </div>
    </div>
  );
}
