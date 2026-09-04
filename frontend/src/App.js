import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
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

function App() {
  return (
    <div className="App min-h-screen bg-[#FBFBFD]">
      <BrowserRouter>
        <AuthProvider>
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Duels />} />
              <Route path="/resultater" element={<Results />} />
              <Route path="/lederboard" element={<Leaderboard />} />
              <Route path="/mine-tips" element={<MyTips />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="*" element={<Duels />} />
            </Routes>
          </main>
          <Toaster position="top-center" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
