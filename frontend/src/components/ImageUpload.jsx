import { useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Upload, Loader2, X } from "lucide-react";

export const ImageUpload = ({ value, onChange, testid, label = "Last opp bilde" }) => {
  const [busy, setBusy] = useState(false);

  const handle = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      onChange(data.url);
      toast.success("Bilde lastet opp");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  };

  return (
    <div className="flex items-center gap-3">
      {value ? (
        <img src={value} alt="" className="w-12 h-12 rounded-full object-cover border border-slate-200 shrink-0" />
      ) : (
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-300 shrink-0"><Upload size={18} /></div>
      )}
      <label data-testid={testid} className="cursor-pointer text-sm font-semibold text-[#D92525] hover:underline flex items-center gap-1.5">
        {busy ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />} {busy ? "Laster opp..." : label}
        <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" className="hidden" onChange={handle} disabled={busy} />
      </label>
      {value && (
        <button type="button" onClick={() => onChange("")} className="text-xs text-slate-400 hover:text-[#D92525] flex items-center gap-0.5">
          <X size={12} /> Fjern
        </button>
      )}
    </div>
  );
};
