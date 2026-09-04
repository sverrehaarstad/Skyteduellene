import { User } from "lucide-react";

export const ShooterAvatar = ({ src, name, badge, size = "md" }) => {
  const dims = size === "lg" ? "w-28 h-28 sm:w-36 sm:h-36" : "w-16 h-16";
  const badgeColor = badge === "1" ? "bg-[#D92525]" : "bg-[#0F172A]";
  return (
    <div className="relative">
      <div className={`${dims} rounded-full overflow-hidden bg-slate-100 border-2 border-white ring-1 ring-slate-200 flex items-center justify-center`}>
        {src ? (
          <img src={src} alt={name} className="w-full h-full object-cover" onError={(e) => { e.currentTarget.style.display = "none"; e.currentTarget.nextSibling.style.display = "flex"; }} />
        ) : null}
        <div className="w-full h-full items-center justify-center text-slate-300" style={{ display: src ? "none" : "flex" }}>
          <User size={size === "lg" ? 56 : 28} />
        </div>
      </div>
      {badge && (
        <span className={`absolute -bottom-1 -right-1 ${badgeColor} text-white w-7 h-7 rounded-full flex items-center justify-center font-black text-sm ring-2 ring-white`} style={{ fontFamily: "Outfit, sans-serif" }}>
          {badge}
        </span>
      )}
    </div>
  );
};
