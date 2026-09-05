import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/Navbar";
import Duels from "@/pages/Duels";
import Results from "@/pages/Results";
import Leaderboard from "@/pages/Leaderboard";
import MyTips from "@/pages/MyTips";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Admin from "@/pages/Admin";
import DuelDetail from "@/pages/DuelDetail";
import ShooterProfile from "@/pages/ShooterProfile";
import Tournaments from "@/pages/Tournaments";
import TournamentDetail from "@/pages/TournamentDetail";
import AuthCallback from "@/pages/AuthCallback";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";

function AppContent() {
  const location = useLocation();
  // Detect Google OAuth callback synchronously during render (prevents race conditions)
  if (location.hash && location.hash.includes("session_id=")) {
    return (
      <>
        <Navbar />
        <AuthCallback />
      </>
    );
  }
  return (
    <>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Duels />} />
          <Route path="/resultater" element={<Results />} />
          <Route path="/lederboard" element={<Leaderboard />} />
          <Route path="/mine-tips" element={<MyTips />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/glemt-passord" element={<ForgotPassword />} />
          <Route path="/reset" element={<ResetPassword />} />
          <Route path="/duell/:id" element={<DuelDetail />} />
          <Route path="/skytter/:name" element={<ShooterProfile />} />
          <Route path="/serier" element={<Tournaments />} />
          <Route path="/serie/:id" element={<TournamentDetail />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="*" element={<Duels />} />
        </Routes>
      </main>
    </>
  );
}

function App() {
  return (
    <div className="App min-h-screen bg-[#FBFBFD]">
      <BrowserRouter>
        <AuthProvider>
          <AppContent />
          <Toaster position="top-center" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
