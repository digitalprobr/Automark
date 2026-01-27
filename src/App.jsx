import { useEffect, useMemo, useState } from "react";
import { Upload, Video, Image as ImageIcon, Play, Download, Clock, CheckCircle, XCircle, Loader } from "lucide-react";

// Prefer an explicit `VITE_API_URL` at build/dev time. When missing,
// use a relative `/api` path so the app works when served from the
// same origin (and avoids mixed-content errors if the frontend is HTTPS).
const API_BASE = import.meta.env.VITE_API_URL || "/api";

const POSITIONS = [
  { value: "top-left", label: "Top Left", icon: "↖" },
  { value: "top-right", label: "Top Right", icon: "↗" },
  { value: "bottom-left", label: "Bottom Left", icon: "↙" },
  { value: "bottom-right", label: "Bottom Right", icon: "↘" },
  { value: "full", label: "Full Screen", icon: "⛶" },
];

export default function App() {
  const [files, setFiles] = useState([]);
  const [logo, setLogo] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [position, setPosition] = useState("bottom-right");
  const [scale, setScale] = useState(0.2);
  
  // Preview states
  const [previewVideoUrl, setPreviewVideoUrl] = useState(null);
  const [previewLogoUrl, setPreviewLogoUrl] = useState(null);
  const [videoMetadata, setVideoMetadata] = useState(null);

  const canSubmit = useMemo(() => files.length > 0 && logo, [files, logo]);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_BASE}/jobs`);
      if (!response.ok) {
        throw new Error("Failed to load jobs");
      }
      const data = await response.json();
      setJobs(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load jobs";
      console.error("fetchJobs error:", err);
      setError(msg);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchJobs, 500);
    const interval = setInterval(fetchJobs, 5000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    // Create preview URL for first video
    if (files.length > 0) {
      const url = URL.createObjectURL(files[0]);
      setPreviewVideoUrl(url);
      
      // Load video metadata to get dimensions
      const video = document.createElement('video');
      video.src = url;
      video.onloadedmetadata = () => {
        setVideoMetadata({
          width: video.videoWidth,
          height: video.videoHeight,
          isVertical: video.videoHeight > video.videoWidth
        });
      };
      
      return () => {
        URL.revokeObjectURL(url);
        setVideoMetadata(null);
      };
    } else {
      setPreviewVideoUrl(null);
      setVideoMetadata(null);
    }
  }, [files]);

  useEffect(() => {
    // Create preview URL for logo
    if (logo) {
      const url = URL.createObjectURL(logo);
      setPreviewLogoUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewLogoUrl(null);
    }
  }, [logo]);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setError("");
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("videos", file));
      formData.append("logo", logo);
      formData.append("position", position);
      formData.append("scale", scale.toString());

      const response = await fetch(`${API_BASE}/jobs/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      await fetchJobs();
      setFiles([]);
      setLogo(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const queuedCount = jobs.filter((job) => job.status === "queued").length;
  const processingCount = jobs.filter((job) => job.status === "processing").length;
  const completedCount = jobs.filter((job) => job.status === "completed").length;

  // Calculate logo position and size for preview
  const getLogoStyle = () => {
    const styles = { position: "absolute", maxWidth: "100%", maxHeight: "100%", zIndex: 0 };
    
    if (position === "full") {
      return { ...styles, top: 0, left: 0, width: "100%", height: "100%", objectFit: "cover" };
    }
    
    // Calculate size based on video height percentage
    const size = `${scale * 100}%`;
    const padding = "15px";  // Fixed 15px padding from corners
    const bottomPadding = "55px";  // Extra padding to avoid video controls bar
    
    switch (position) {
      case "top-left":
        return { ...styles, top: padding, left: padding, height: size };
      case "top-right":
        return { ...styles, top: padding, right: padding, height: size };
      case "bottom-left":
        return { ...styles, bottom: bottomPadding, left: padding, height: size };
      case "bottom-right":
      default:
        return { ...styles, bottom: bottomPadding, right: padding, height: size };
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      <header className="border-b border-slate-800/50 bg-slate-950/50 backdrop-blur-xl">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20">
                <Video className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium uppercase tracking-wider text-cyan-400">Automark</p>
                <h1 className="text-2xl font-bold">Bulk Video Watermarking</h1>
              </div>
            </div>
            <button className="rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-cyan-500/30 transition hover:shadow-cyan-500/50">
              Upgrade Pro
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-auto max-w-7xl px-6 pt-6">
          <div className="rounded-xl border border-red-500/50 bg-red-500/10 px-4 py-3 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <XCircle className="h-5 w-5 text-red-400" />
              <p className="text-sm text-red-200">{error}</p>
            </div>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid gap-8 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-800/50 bg-gradient-to-br from-cyan-500/10 via-slate-900/40 to-blue-500/10 backdrop-blur-xl p-6 shadow-2xl">
              <h3 className="mb-4 text-lg font-bold">Processing Queue</h3>
              <div className="mb-6 grid grid-cols-3 gap-3">
                <div className="rounded-xl bg-slate-950/80 p-4 text-center border border-slate-800">
                  <div className="mb-2 text-2xl font-bold text-yellow-400">{queuedCount}</div>
                  <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
                    <Clock className="h-3 w-3" />Queued
                  </div>
                </div>
                <div className="rounded-xl bg-slate-950/80 p-4 text-center border border-slate-800">
                  <div className="mb-2 text-2xl font-bold text-blue-400">{processingCount}</div>
                  <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
                    <Loader className="h-3 w-3 animate-spin" />Processing
                  </div>
                </div>
                <div className="rounded-xl bg-slate-950/80 p-4 text-center border border-slate-800">
                  <div className="mb-2 text-2xl font-bold text-green-400">{completedCount}</div>
                  <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
                    <CheckCircle className="h-3 w-3" />Done
                  </div>
                </div>
              </div>
              <button onClick={handleSubmit} disabled={!canSubmit || isSubmitting} className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 text-base font-bold text-white shadow-lg shadow-cyan-500/30 transition hover:shadow-cyan-500/50 disabled:cursor-not-allowed disabled:from-slate-700 disabled:to-slate-700 disabled:shadow-none disabled:text-slate-400">
                {isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader className="h-5 w-5 animate-spin" />Uploading...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Play className="h-5 w-5" />Start Processing {files.length > 0 && `(${files.length} videos)`}
                  </span>
                )}
              </button>
            </div>

            <div className="rounded-2xl border border-slate-800/50 bg-slate-900/40 backdrop-blur-xl p-6 shadow-2xl">
              <h3 className="mb-4 text-lg font-bold flex items-center gap-2">
                <Upload className="h-5 w-5 text-cyan-400" />
                Upload Videos
              </h3>
              <label className="group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-950/50 p-8 transition hover:border-cyan-500 hover:bg-slate-950">
                <Video className="h-10 w-10 text-slate-600 group-hover:text-cyan-400 transition mb-3" />
                <span className="text-sm font-semibold text-slate-300 group-hover:text-cyan-400 transition">Click to select vertical videos</span>
                <span className="mt-1 text-xs text-slate-500">MP4, MOV • 1080x1920 pixels (will crop if needed)</span>
                <input type="file" multiple accept="video/*" className="hidden" onChange={(e) => setFiles(Array.from(e.target.files || []))} />
              </label>
              {files.length > 0 && (
                <div className="mt-4 space-y-2">
                  {files.slice(0, 3).map((file, i) => (
                    <div key={i} className="flex items-center gap-3 rounded-lg bg-slate-800/50 px-3 py-2">
                      <Video className="h-4 w-4 text-cyan-400 flex-shrink-0" />
                      <span className="text-sm text-slate-300 truncate flex-1">{file.name}</span>
                      <span className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
                    </div>
                  ))}
                  {files.length > 3 && <div className="text-center text-xs text-slate-500 py-2">+{files.length - 3} more files</div>}
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-slate-800/50 bg-slate-900/40 backdrop-blur-xl p-6 shadow-2xl">
              <h3 className="mb-4 text-lg font-bold flex items-center gap-2">
                <ImageIcon className="h-5 w-5 text-cyan-400" />
                Upload Logo
              </h3>
              <label className="group relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-950/50 p-8 transition hover:border-cyan-500 hover:bg-slate-950">
                <ImageIcon className="h-10 w-10 text-slate-600 group-hover:text-cyan-400 transition mb-3" />
                <span className="text-sm font-semibold text-slate-300 group-hover:text-cyan-400 transition">Click to select logo</span>
                <span className="mt-1 text-xs text-slate-500">PNG with transparency recommended</span>
                <input type="file" accept="image/*" className="hidden" onChange={(e) => setLogo(e.target.files?.[0] || null)} />
              </label>
              {logo && (
                <div className="mt-4 flex items-center gap-3 rounded-lg bg-slate-800/50 px-3 py-2">
                  <ImageIcon className="h-4 w-4 text-cyan-400 flex-shrink-0" />
                  <span className="text-sm text-slate-300 truncate flex-1">{logo.name}</span>
                  <span className="text-xs text-slate-500">{(logo.size / 1024).toFixed(1)} KB</span>
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-slate-800/50 bg-slate-900/40 backdrop-blur-xl p-6 shadow-2xl">
              <h3 className="mb-4 text-lg font-bold">Watermark Position</h3>
              <div className="grid grid-cols-5 gap-3">
                {POSITIONS.map((pos) => (
                  <button
                    key={pos.value}
                    onClick={() => setPosition(pos.value)}
                    className={`group relative overflow-hidden rounded-xl border-2 p-4 transition-all ${
                      position === pos.value ? "border-cyan-500 bg-cyan-500/20 shadow-lg shadow-cyan-500/20" : "border-slate-700 bg-slate-800/50 hover:border-slate-600"
                    }`}
                  >
                    <div className="flex flex-col items-center gap-2">
                      <span className="text-2xl">{pos.icon}</span>
                      <span className="text-xs font-semibold">{pos.label}</span>
                    </div>
                    {position === pos.value && <div className="absolute inset-0 border-2 border-cyan-400 rounded-xl animate-pulse" />}
                  </button>
                ))}
              </div>
              <div className="mt-6">
                <div className="mb-3 flex items-center justify-between">
                  <label className="text-sm font-semibold text-slate-300">Logo Size</label>
                  <span className="rounded-lg bg-slate-800 px-3 py-1 text-xs font-mono text-cyan-400">{Math.round(scale * 100)}%</span>
                </div>
                <input type="range" min="0.05" max="0.5" step="0.05" value={scale} onChange={(e) => setScale(parseFloat(e.target.value))} disabled={position === "full"} className="w-full accent-cyan-500 disabled:opacity-50" />
                <div className="mt-2 flex justify-between text-xs text-slate-500">
                  <span>Small</span>
                  <span>Large</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="sticky top-8 rounded-2xl border border-slate-800/50 bg-slate-900/40 backdrop-blur-xl p-6 shadow-2xl">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Play className="h-5 w-5 text-cyan-400" />
                  Live Preview
                </h2>
                <div className="flex items-center gap-2">
                  {videoMetadata && (
                    <>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        videoMetadata.width === 1080 && videoMetadata.height === 1920
                          ? "bg-green-500/20 text-green-400" 
                          : "bg-yellow-500/20 text-yellow-400"
                      }`}>
                        📱 {videoMetadata.width}x{videoMetadata.height}
                      </span>
                      {(videoMetadata.width !== 1080 || videoMetadata.height !== 1920) && (
                        <span className="rounded-full bg-yellow-500/20 px-3 py-1 text-xs font-semibold text-yellow-400">
                          Will crop to 1080x1920
                        </span>
                      )}
                    </>
                  )}
                  {previewVideoUrl && previewLogoUrl && (
                    <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs font-semibold text-green-400">Ready</span>
                  )}
                </div>
              </div>
              <div className="flex justify-center">
                <div className="relative w-80 overflow-hidden rounded-xl bg-slate-950 border border-slate-800" style={{ aspectRatio: '9/16' }}>
                  {previewVideoUrl ? (
                    <>
                      <video src={previewVideoUrl} className="h-full w-full object-cover" controls loop muted />
                      {previewLogoUrl && (
                        <img src={previewLogoUrl} alt="Logo preview" className="pointer-events-none" style={getLogoStyle()} />
                      )}
                    </>
                  ) : (
                  <div className="flex h-full items-center justify-center">
                    <div className="text-center text-slate-500">
                      <Video className="mx-auto h-12 w-12 mb-3 opacity-50" />
                        <p className="text-sm">Upload a vertical video</p>
                        <p className="text-xs mt-1 text-slate-600">1080x1920 pixels</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              {files.length > 1 && (
                <p className="mt-4 text-xs text-slate-400 text-center">
                  Previewing first video • {files.length} videos will be processed with these settings
                </p>
              )}
            </div>
          </div>
        </div>

        {jobs.length > 0 && (
          <div className="mt-8">
            <h2 className="mb-6 text-2xl font-bold">Recent Jobs</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {jobs.map((job) => (
                <div key={job.id} className="group rounded-xl border border-slate-800/50 bg-slate-900/40 backdrop-blur-xl p-5 shadow-lg transition hover:border-slate-700">
                  <div className="mb-3 flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="truncate font-semibold text-slate-200">{job.input_name}</h4>
                      <p className="mt-1 text-xs text-slate-500">Logo: {job.logo_name}</p>
                    </div>
                    <span className={`ml-2 flex-shrink-0 rounded-full px-3 py-1 text-xs font-bold ${
                      job.status === "processing" ? "bg-blue-500/20 text-blue-300" : job.status === "completed" ? "bg-green-500/20 text-green-300" : job.status === "failed" ? "bg-red-500/20 text-red-300" : "bg-yellow-500/20 text-yellow-300"
                    }`}>{job.status}</span>
                  </div>
                  {job.status === "processing" && (
                    <div className="space-y-2">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div 
                          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300" 
                          style={{ width: `${job.progress || 0}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-blue-400 flex items-center gap-2">
                        <Loader className="h-3 w-3 animate-spin" />
                        Processing video... {job.progress || 0}%
                      </p>
                    </div>
                  )}
                  {job.status === "completed" && (
                    <div className="space-y-3">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full w-full rounded-full bg-gradient-to-r from-green-500 to-emerald-500"></div>
                      </div>
                      <a href={`${API_BASE}/jobs/${job.id}/download`} download className="flex items-center justify-center gap-2 rounded-lg bg-green-500/20 px-4 py-2 text-sm font-semibold text-green-300 border border-green-500/30 transition hover:bg-green-500/30">
                        <Download className="h-4 w-4" />Download
                      </a>
                    </div>
                  )}
                  {job.status === "queued" && (
                    <div className="space-y-2">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full w-1/12 rounded-full bg-yellow-500/50"></div>
                      </div>
                      <p className="text-xs text-slate-400 flex items-center gap-2"><Clock className="h-3 w-3" />Waiting in queue...</p>
                    </div>
                  )}
                  {job.status === "failed" && (
                    <div className="space-y-2">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                        <div className="h-full w-full rounded-full bg-red-500"></div>
                      </div>
                      <p className="text-xs text-red-400 flex items-center gap-2"><XCircle className="h-3 w-3" />Processing failed</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
