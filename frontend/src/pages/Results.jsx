import { useEffect, useState } from "react";
import api from "@/lib/api";
import { ListChecks } from "lucide-react";

const outcomeLabel = (d) => {
  if (d.outcome === "1") return d.shooter1;
  if (d.outcome === "2") return d.shooter2;
  return "Uavgjort";
};

export default function Results() {
  const [duels, setDuels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/duels", { params: { status: "finished" } }).then(({ data }) => {
      setDuels(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <ListChecks size={22} className="text-[#D92525]" />
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Resultatliste</h1>
      </div>

      {loading ? (
        <p className="text-slate-500">Laster...</p>
      ) : duels.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-xl" data-testid="no-results">
          <p className="text-slate-500 font-semibold">Ingen avsluttede dueller ennå.</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="results-list">
          {duels.map((d) => (
            <div key={d.id} className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5" data-testid={`result-${d.id}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#B91C1C] bg-[#FEF2F2] px-2.5 py-1 rounded-full">{d.discipline}</span>
                <span className="text-xs text-slate-400">{d.venue}</span>
              </div>
              <div className="grid grid-cols-3 items-center gap-2">
                <div className={`text-left ${d.outcome === "1" ? "font-black text-[#D92525]" : "font-semibold text-slate-700"}`}>
                  <span className="text-xs font-mono text-slate-400 block">1</span>
                  {d.shooter1}
                  <span className="block font-mono text-lg text-slate-900">{d.score1 || "-"}</span>
                </div>
                <div className="text-center">
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Vinner</span>
                  <span className="inline-block mt-1 px-3 py-1 rounded-full bg-[#0F172A] text-white text-sm font-bold" style={{ fontFamily: "Outfit, sans-serif" }}>
                    {outcomeLabel(d)}
                  </span>
                </div>
                <div className={`text-right ${d.outcome === "2" ? "font-black text-[#D92525]" : "font-semibold text-slate-700"}`}>
                  <span className="text-xs font-mono text-slate-400 block">2</span>
                  {d.shooter2}
                  <span className="block font-mono text-lg text-slate-900">{d.score2 || "-"}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
