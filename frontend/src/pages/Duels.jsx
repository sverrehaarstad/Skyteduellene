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

  const load = useCallback(async () => {
    const { data } = await api.get("/duels", { params: { status: "open" } });
    setDuels(data);
    if (user) {
      const res = await api.get("/my-tips");
      const map = {};
      res.data.forEach((t) => (map[t.duel.id] = t.pick));
      setMyTips(map);
    }
    setLoading(false);
  }, [user]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    api.get("/settings").then(({ data }) => data.hero_image && setHero(data.hero_image)).catch(() => {});
  }, []);

  const onTipped = () => { load(); refreshMe(); };

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
            Duellene fra DFS-banen. Velg vinner (1), uavgjort (U) eller utfordrer (2) – samle poeng og klatre på lederboardet.
          </p>
        </div>
      </div>

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
          {duels.map((d) => (
            <DuelCard key={d.id} duel={d} myPick={myTips[d.id]} onTipped={onTipped} />
          ))}
        </div>
      )}
    </div>
  );
}
