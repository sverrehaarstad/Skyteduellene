import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { ShooterAvatar } from "@/components/ShooterAvatar";
import { ArrowLeft, Target as TargetIcon } from "lucide-react";

export default function ShooterProfile() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    api.get(`/shooters/${encodeURIComponent(name)}`).then(({ data }) => setData(data)).catch(() => setNotFound(true));
  }, [name]);

  if (notFound) return <div className="max-w-2xl mx-auto px-4 py-16 text-slate-500">Fant ikke skytteren.</div>;
  if (!data) return <div className="max-w-2xl mx-auto px-4 py-16 text-slate-500">Laster...</div>;

  const { record } = data;
  const stat = [
    { label: "Seiere", value: record.wins, color: "text-[#16A34A]" },
    { label: "Uavgjort", value: record.draws, color: "text-slate-600" },
    { label: "Tap", value: record.losses, color: "text-[#D92525]" },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6" data-testid="shooter-profile">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-900 mb-5">
        <ArrowLeft size={16} /> Tilbake
      </button>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-center gap-6">
        <ShooterAvatar src={data.image} name={data.name} size="lg" />
        <div className="text-center sm:text-left flex-1">
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>{data.name}</h1>
          <div className="flex justify-center sm:justify-start gap-6 mt-4">
            {stat.map((s) => (
              <div key={s.label} className="text-center">
                <p className={`font-mono font-bold text-2xl ${s.color}`}>{s.value}</p>
                <p className="text-xs uppercase tracking-wider text-slate-500">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <h2 className="flex items-center gap-2 font-bold text-slate-900 mt-8 mb-4"><TargetIcon size={18} className="text-[#D92525]" /> Dueller ({data.duels.length})</h2>
      {data.duels.length === 0 ? (
        <p className="text-slate-500 text-sm">Ingen dueller ennå.</p>
      ) : (
        <div className="space-y-3" data-testid="shooter-duels">
          {data.duels.map((d) => {
            const opponent = d.shooter1 === data.name ? d.shooter2 : d.shooter1;
            return (
              <Link key={d.id} to={`/duell/${d.id}`} className="block bg-white border border-slate-200 rounded-xl p-4 hover:border-[#FCA5A5] transition-colors" data-testid={`shooter-duel-${d.id}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs text-[#B91C1C] font-semibold uppercase tracking-wider">{d.discipline}</span>
                    <p className="font-bold text-slate-900 text-sm">vs {opponent}</p>
                  </div>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${d.status === "finished" ? "bg-slate-100 text-slate-600" : "bg-green-50 text-[#16A34A]"}`}>
                    {d.status === "finished" ? "Avsluttet" : "Åpen"}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
