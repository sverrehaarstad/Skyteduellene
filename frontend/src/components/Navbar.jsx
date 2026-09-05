import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Target } from "@/components/Target";
import { Crosshair, LogOut, Trophy, ListChecks, Swords, ClipboardList, Shield, Medal } from "lucide-react";

const NavLink = ({ to, children, active, testid }) => (
  <Link
    to={to}
    data-testid={testid}
    className={`px-3 py-2 text-sm font-semibold rounded-md transition-colors duration-200 ${
      active ? "bg-[#FEF2F2] text-[#B91C1C]" : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
    }`}
  >
    {children}
  </Link>
);

export const Navbar = () => {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const links = [
    { to: "/", label: "Dueller", icon: Swords, testid: "nav-duels" },
    { to: "/resultater", label: "Resultater", icon: ListChecks, testid: "nav-results" },
    { to: "/serier", label: "Serier", icon: Medal, testid: "nav-tournaments" },
    { to: "/lederboard", label: "Lederboard", icon: Trophy, testid: "nav-leaderboard" },
  ];
  if (user) links.push({ to: "/mine-tips", label: "Mine Tips", icon: ClipboardList, testid: "nav-mytips" });
  if (user?.role === "admin") links.push({ to: "/admin", label: "Admin", icon: Shield, testid: "nav-admin" });

  return (
    <header className="sticky top-0 z-50 bg-white/85 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2 shrink-0" data-testid="brand-logo">
          <Target size={30} />
          <span className="font-black text-lg tracking-tight text-slate-900" style={{ fontFamily: "Outfit, sans-serif" }}>
            Skyte<span className="text-[#D92525]">duellene</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} active={pathname === l.to} testid={l.testid}>
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <div className="hidden sm:flex items-center gap-1.5 bg-[#0F172A] text-white px-3 py-1.5 rounded-full" data-testid="user-points">
                <Crosshair size={14} className="text-[#EF4444]" />
                <span className="font-mono font-bold text-sm">{user.points}</span>
                <span className="text-xs text-slate-300">poeng</span>
              </div>
              <span className="hidden lg:block text-sm font-semibold text-slate-700 max-w-[120px] truncate" data-testid="user-name">{user.name}</span>
              <button
                onClick={() => { logout(); navigate("/"); }}
                data-testid="logout-btn"
                className="p-2 text-slate-500 hover:text-[#D92525] hover:bg-[#FEF2F2] rounded-md transition-colors"
                title="Logg ut"
              >
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <>
              <Link to="/login" data-testid="nav-login" className="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-slate-900 rounded-md">
                Logg inn
              </Link>
              <Link to="/register" data-testid="nav-register" className="px-4 py-2 text-sm font-bold text-white bg-[#D92525] hover:bg-[#B91C1C] rounded-md transition-colors">
                Registrer
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Mobile nav */}
      <nav className="md:hidden flex items-center gap-1 px-3 pb-2 overflow-x-auto border-t border-slate-100">
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} active={pathname === l.to} testid={`m-${l.testid}`}>
            {l.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
};
