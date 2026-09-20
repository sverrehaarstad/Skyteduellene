import { useEffect, useState } from "react";
import api from "@/lib/api";
import { ListChecks, Search } from "lucide-react";

const outcomeLabel = (d) => {
  if (d.outcome === "1") return d.shooter1;
  if (d.outcome === "2") return d.shooter2;
  if (d.outcome === "X") return "Uavgjort";

  const hasStarted = d.start_at
    ? new Date() >= new Date(d.start_at)
    : false;

  return hasStarted ? "Venter på resultat" : "Live";
};

const outcomeStyle = (d) => {
  if (d.outcome) {
    return "bg-amber-100 text-amber-800 border border-amber-300";
  }

  const hasStarted = d.start_at
    ? new Date() >= new Date(d.start_at)
    : false;

  return hasStarted
    ? "bg-red-100 text-red-700 border border-red-200"
    : "bg-green-100 text-green-700 border border-green-200";
};

export default function Results() {
  const [duels, setDuels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.get("/duels", { params: { status: "finished" } }).then(({ data }) => {
      setDuels(data);
      setLoading(false);
    });
  }, []);

  const filteredDuels = duels.filter((d) => {
    const searchText = search.trim().toLowerCase();

    if (!searchText) return true;

    return (
      d.shooter1?.toLowerCase().includes(searchText) ||
      d.shooter2?.toLowerCase().includes(searchText)
    );
  });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <ListChecks size={22} className="text-[#D92525]" />
        <h1
          className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900"
          style={{ fontFamily: "Outfit, sans-serif" }}
        >
          Resultatliste
        </h1>
      </div>

      <div className="relative mb-6">
        <Search
          size={18}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Søk etter deltaker..."
          className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl bg-white focus:outline-none focus:border-[#D92525]"
        />
      </div>

      {loading ? (
        <p className="text-slate-500">Laster...</p>
      ) : filteredDuels.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-xl">
          <p className="text-slate-500 font-semibold">
            {search
              ? "Ingen dueller funnet for denne deltakeren."
              : "Ingen avsluttede dueller ennå."}
          </p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="results-list">
          {filteredDuels.map((d) => (
            <div
              key={d.id}
              className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5"
              data-testid={`result-${d.id}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-[#B91C1C] bg-[#FEF2F2] px-2.5 py-1 rounded-full">
                  {d.discipline}
                </span>

                <span className="text-xs text-slate-400">
                  {d.venue}
                </span>
              </div>

              <div className="grid grid-cols-3 items-center gap-2">
                <div
                  className={`text-left ${
                    d.outcome === "1"
                      ? "font-black text-amber-600"
                      : "font-semibold text-slate-700"
                  }`}
                >
                  <span className="text-xs font-mono text-slate-400 block">
                    1
                  </span>

                  <div className="flex items-center gap-2">
  {d.shooter1_img && (
    <img
      src={d.shooter1_img}
      alt={d.shooter1}
      className="w-10 h-10 rounded-full object-cover border border-slate-200"
    />
  )}

  <div>
    <span className="block">{d.shooter1}</span>
    {d.shooter1_club && (
      <span className="block text-xs font-normal text-slate-500">
        {d.shooter1_club}
      </span>
    )}
    {d.shooter1_class && (
      <span className="block text-xs font-normal text-slate-500">
        Klasse {d.shooter1_class}
      </span>
    )}
  </div>
</div>

                  <span className="block font-mono text-lg text-slate-900">
                    {d.score1 || "-"}
                  </span>
                </div>

                <div className="text-center">
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 block">
                    {d.outcome ? "Vinner" : "Status"}
                  </span>

                  <span
                    className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-bold ${outcomeStyle(
                      d
                    )}`}
                    style={{ fontFamily: "Outfit, sans-serif" }}
                  >
                    {outcomeLabel(d)}
                  </span>
                </div>

                <div
                  className={`text-right ${
                    d.outcome === "2"
                      ? "font-black text-amber-600"
                      : "font-semibold text-slate-700"
                  }`}
                >
                  <span className="text-xs font-mono text-slate-400 block">
                    2
                  </span>

<div className="flex items-center justify-end gap-2">
  <div className="text-right">
    <span className="block">{d.shooter2}</span>
    {d.shooter2_club && (
      <span className="block text-xs font-normal text-slate-500">
        {d.shooter2_club}
      </span>
    )}
    {d.shooter2_class && (
      <span className="block text-xs font-normal text-slate-500">
        Klasse {d.shooter2_class}
      </span>
    )}
  </div>

  {d.shooter2_img && (
    <img
      src={d.shooter2_img}
      alt={d.shooter2}
      className="w-10 h-10 rounded-full object-cover border border-slate-200"
    />
  )}
</div>
                  <span className="block font-mono text-lg text-slate-900">
                    {d.score2 || "-"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
