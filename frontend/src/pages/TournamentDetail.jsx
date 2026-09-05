import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { ArrowLeft, Trophy, Crown, ListChecks } from "lucide-react";

const medal = ["#EAB308", "#94A3B8", "#B45309"];

export default function TournamentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api.get(`/tournaments/${id}`).then(({ data }) => setData(data)).catch(() => setNotFound(true));
  }, [id]);

  if (notFound) return <div className="max-w-2xl mx-auto px-4 py-16 text-slate-500">Fant ikke serien.</div>;
  if (!data) return <div className="max-w-2xl mx-auto px-4 py-16 text-slate-500">Laster...</div>;

  const { tournament, standings, duels, winners, finished_count, duel_count } = data;
  const winnerList = winners || (data.winner ? [data.winner] : []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6" data-testid="tournament-detail">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-900 mb-5">
        <ArrowLeft size={16} /> Tilbake
      </button>

      <div className="bg-[#0F172A] text-white rounded-2xl p-6 sm:p-8 mb-6">
        <div className="flex items-center gap-2 text-[#EAB308] mb-2">
          <Trophy size={18} />
          <span className="text-xs font-semibold uppercase tracking-widest">{tournament.season || "Sesong"}</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black tracking-tight" style={{ fontFamily: "Outfit, sans-serif" }}>{tournament.name}</h1>
        <p className="text-slate-300 text-sm mt-2">{finished_count} av {duel_count} {duel_count === 1 ? "duell" : "dueller"} avgjort</p>

        {winnerList.length > 0 ? (
          <div className="mt-5 bg-white/10 rounded-xl p-4" data-testid="tournament-winner">
            <div className="flex items-center gap-2 text-[#EAB308] mb-2">
              <Crown size={20} />
              <p className="text-xs uppercase tracking-wider">{winnerList.length > 1 ? "Delt totalseier" : "Totalvinner"}</p>
            </div>
            <div className="space-y-2">
              {winnerList.map((w) => (
                <div key={w.id} className="flex items-center gap-3" data-testid={`winner-${w.id}`}>
                  <Crown size={22} className="text-[#EAB308] shrink-0" />
                  <p className="text-lg font-black" style={{ fontFamily: "Outfit, sans-serif" }}>{w.name}</p>
                  <span className="ml-auto font-mono font-bold text-xl text-[#EAB308]">{w.points} p</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-300" data-testid="no-winner">Totalvinner kåres når alle duellene er avgjort.</p>
        )}
      </div>

      {/* Standings */}
      <h2 className="flex items-center gap-2 font-bold text-slate-900 mb-3"><Trophy size={18} className="text-[#D92525]" /> Sesongtabell</h2>
      {standings.length === 0 ? (
        <p className="text-slate-500 text-sm mb-6">Ingen tips lagt inn i denne serien ennå.</p>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden mb-8" data-testid="tournament-standings">
          <div className="grid grid-cols-12 px-4 py-3 bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <div className="col-span-1">#</div>
            <div className="col-span-5">Tipper</div>
            <div className="col-span-2 text-center">Riktige</div>
            <div className="col-span-2 text-center">Treff %</div>
            <div className="col-span-2 text-right">Poeng</div>
          </div>
          {standings.map((r, i) => (
            <div key={r.id} className={`grid grid-cols-12 px-4 py-3 items-center border-b border-slate-100 last:border-0 ${i < 3 ? "bg-[#FBFBFD]" : ""}`} data-testid={`ts-row-${i}`}>
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

      {/* Duels in season */}
      <h2 className="flex items-center gap-2 font-bold text-slate-900 mb-3"><ListChecks size={18} className="text-[#D92525]" /> Dueller i serien</h2>
      <div className="space-y-3" data-testid="tournament-duels">
        {duels.map((d) => (
          <Link key={d.id} to={`/duell/${d.id}`} className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-4 hover:border-[#FCA5A5] transition-colors">
            <div>
              <span className="text-xs text-[#B91C1C] font-semibold uppercase tracking-wider">{d.discipline}</span>
              <p className="font-bold text-slate-900 text-sm">{d.shooter1} vs {d.shooter2}</p>
            </div>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${d.status === "finished" ? "bg-slate-100 text-slate-600" : "bg-green-50 text-[#16A34A]"}`}>
              {d.status === "finished" ? "Avsluttet" : "Åpen"}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
