import { useEffect, useState } from "react";
import { Timer } from "lucide-react";

function diff(target) {
  const ms = new Date(target).getTime() - Date.now();
  if (isNaN(ms)) return null;
  return ms;
}

export const Countdown = ({ startAt, className = "" }) => {
  const [ms, setMs] = useState(() => diff(startAt));

  useEffect(() => {
    setMs(diff(startAt));
    const id = setInterval(() => setMs(diff(startAt)), 1000);
    return () => clearInterval(id);
  }, [startAt]);

  if (ms === null) return null;

  if (ms <= 0) {
    return (
      <span className={`inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#16A34A] ${className}`} data-testid="countdown-started">
        <span className="w-2 h-2 rounded-full bg-[#16A34A] animate-pulse" /> I gang
      </span>
    );
  }

  const s = Math.floor(ms / 1000);
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;

  const parts = [];
  if (d > 0) parts.push([d, "d"]);
  if (d > 0 || h > 0) parts.push([h, "t"]);
  parts.push([m, "m"]);
  if (d === 0) parts.push([sec, "s"]);

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono font-bold text-[#D92525] ${className}`} data-testid="countdown">
      <Timer size={13} className="text-[#D92525]" />
      {parts.map(([v, u], i) => (
        <span key={i}>{String(v).padStart(2, "0")}<span className="text-slate-400 text-[0.85em]">{u}</span></span>
      ))}
    </span>
  );
};
