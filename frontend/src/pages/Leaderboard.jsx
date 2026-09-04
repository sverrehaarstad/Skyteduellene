import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Trophy } from "lucide-react";

const medal = ["#EAB308", "#94A3B8", "#B45309"];

export default function Leaderboard() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/leaderboard").then(({ data }) => {
      setRows(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <Trophy size={22} className="text-[#D92525]" />
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>Lederboard</h1>
      </div>

      {loading ? (
        <p className="text-slate-500">Laster...</p>
      ) : rows.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-xl" data-testid="no-leaderboard">
          <p className="text-slate-500 font-semibold">Ingen tippere ennå.</p>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="leaderboard-table">
          <div className="grid grid-cols-12 px-4 py-3 bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <div className="col-span-1">#</div>
            <div className="col-span-5">Tipper</div>
            <div className="col-span-2 text-center">Riktige</div>
            <div className="col-span-2 text-center">Treff %</div>
            <div className="col-span-2 text-right">Poeng</div>
          </div>
          {rows.map((r, i) => (
            <div key={r.id} className={`grid grid-cols-12 px-4 py-3 items-center border-b border-slate-100 last:border-0 ${i < 3 ? "bg-[#FBFBFD]" : ""}`} data-testid={`lb-row-${i}`}>
              <div className="col-span-1">
                <span className="w-6 h-6 flex items-center justify-center rounded-full text-xs font-black text-white" style={{ fontFamily: "Outfit, sans-serif", background: medal[i] || "#0F172A" }}>{i + 1}</span>
              </div>
              <div className="col-span-5 font-bold text-slate-900 truncate">{r.name}</div>
              <div className="col-span-2 text-center font-mono text-slate-700">{r.correct}/{r.total_tips}</div>
              <div className="col-span-2 text-center font-mono text-slate-500 text-sm">{r.accuracy}%</div>
              <div className="col-span-2 text-right font-mono font-bold text-lg text-[#D92525]">{r.points}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
