import { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { DuelCard } from "@/components/DuelCard";
import { Target } from "@/components/Target";
import { Swords } from "lucide-react";

const DEFAULT_HERO = "https://customer-assets-4nw71qhi.emergentagent.net/job_duel-shooter-tips/artifacts/7tyyrc1x_Stangskyting1.webp";

export default function Duels() {
  const { user, refreshMe } = useAuth();
  const [duels, setDuels] = useState([]);
  const [myTips, setMyTips] = useState({});
  const [loading, setLoading] = useState(true);
  const [hero, setHero] = useState(DEFAULT_HERO);
  const [tournaments, setTournaments] = useState([]);
const [selectedTournament, setSelectedTournament] = useState(null);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/duels", { params: { status: "open" } });
      // Håndter både array og object format
      const duelsList = Array.isArray(data) ? data : (data.dueller || []);
      const activeDuels = duelsList
  .filter((duel) => duel.status !== "finished")
  .sort((a, b) => {
    if (!a.start_at) return 1;
    if (!b.start_at) return -1;
    return new Date(a.start_at) - new Date(b.start_at);
  });

setDuels(activeDuels);
      if (user) {
        const res = await api.get("/my-tips");
        const map = {};
        res.data.forEach((t) => (map[t.duel.id] = t.pick));
        setMyTips(map);
      }
    } catch (error) {
      console.error("Feil ved henting av dueller:", error);
    }
    setLoading(false);
  }, [user]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    api.get("/settings").then(({ data }) => data.hero_image && setHero(data.hero_image)).catch(() => {});
  }, []);
  useEffect(() => {
  api.get("/tournaments")
    .then(({ data }) => setTournaments(data))
    .catch(() => setTournaments([]));
}, [user]);

  const onTipped = () => { load(); refreshMe(); };
  const activeTournaments = tournaments.filter((t) =>
  duels.some((duel) =>
    duel.tournament_ids?.some(
      (id) => Number(id) === Number(t.id)
    )
  )
);

  const visibleDuels = selectedTournament
  ? duels.filter((duel) =>
      duel.tournament_ids?.some(
        (id) => Number(id) === Number(selectedTournament)
      )
    )
  : duels;
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
      {/* Hero */}
      <div className="relative rounded-2xl overflow-hidden mb-8 border border-slate-200">
        <img src={hero} alt="DFS skyting" className="w-full h-56 sm:h-72 object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t sm:bg-gradient-to-r from-white via-white/90 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-center px-6 sm:px-10 max-w-xl">
          <div className="flex items-center gap-2 mb-3">
            <Target size={26} />
            <span className="text-xs font-bold uppercase tracking-widest text-[#B91C1C]">Skyteduellene · DFS</span>
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-none" style={{ fontFamily: "Outfit, sans-serif" }}>
            Tipp Norges<br /><span className="text-[#D92525]">skarpeste skyttere</span>
          </h1>
          <p className="text-base text-slate-600 mt-4 max-w-md">
            Duellene fra DFS-banen. Velg vinner (1), uavgjort (U) eller utfordrer (2) – samle poeng og klatre på topplisten.
          </p>
        </div>
      </div>
{activeTournaments.length > 0 && (
  <div className="mb-5">
    <div className="flex items-center gap-4 overflow-x-auto pb-2">
      <span className="text-sm font-semibold text-muted-foreground whitespace-nowrap">
        Aktive konkurranser
      </span>

      {activeTournaments.map((t) => (
        <button
          key={t.id}
          onClick={() =>
            setSelectedTournament(
              selectedTournament === t.id ? null : t.id
            )
          }
          className={`px-4 py-2 rounded-lg whitespace-nowrap border transition ${
            selectedTournament === t.id
              ? "bg-primary text-primary-foreground border-primary"
              "bg-[#D92525] text-white border-[#D92525] hover:bg-[#B91C1C]"
          }`}
        >
          {t.name}
        </button>
      ))}
    </div>
  </div>
)}
      <div className="flex items-center gap-2 mb-5">
        <Swords size={22} className="text-[#D92525]" />
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Aktive Dueller</h2>
      </div>

      {loading ? (
        <p className="text-slate-500" data-testid="duels-loading">Laster dueller...</p>
      ) : duels.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-xl" data-testid="no-duels">
          <Target size={48} className="mx-auto mb-4 opacity-40" />
          <p className="text-slate-500 font-semibold">Ingen aktive dueller akkurat nå.</p>
          <p className="text-slate-400 text-sm mt-1">Kom tilbake senere for nye tippemuligheter!</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="duels-grid">
          {visibleDuels.map((d) => (
            <DuelCard key={d.id} duel={d} myPick={myTips[d.id]} onTipped={onTipped} />
          ))}
        </div>
      )}
    </div>
  );
}
