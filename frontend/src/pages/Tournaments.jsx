import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Trophy, ChevronRight } from "lucide-react";

export default function Tournaments() {
  const [tours, setTours] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/tournaments").then(({ data }) => { setTours(data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <Trophy size={22} className="text-[#D92525]" />
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Serier & Sesonger</h1>
      </div>

      {loading ? (
        <p className="text-slate-500">Laster...</p>
      ) : tours.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-xl" data-testid="no-tournaments">
          <p className="text-slate-500 font-semibold">Ingen serier opprettet ennå.</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="tournaments-list">
          {tours.map((t) => (
            <Link key={t.id} to={`/serie/${t.id}`} data-testid={`tournament-${t.id}`} className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-5 hover:border-[#FCA5A5] transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-11 h-11 rounded-full bg-[#FEF2F2] flex items-center justify-center">
                  <Trophy size={20} className="text-[#EAB308]" />
                </div>
                <div>
                  <p className="font-bold text-slate-900">{t.name}</p>
                  <p className="text-sm text-slate-500">{t.season ? `${t.season} · ` : ""}{t.duel_count} {t.duel_count === 1 ? "duell" : "dueller"}</p>
                </div>
              </div>
              <ChevronRight size={20} className="text-slate-300" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
