"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { triageSymptoms } from "@/lib/api";

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "ja", name: "Japanese" },
  { code: "th", name: "Thai" },
  { code: "zh", name: "Chinese" },
  { code: "ko", name: "Korean" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "es", name: "Spanish" },
  { code: "ar", name: "Arabic" },
  { code: "hi", name: "Hindi" },
];

const QUICK_SYMPTOMS = [
  "Fever and chills",
  "Chest pain",
  "Severe headache",
  "Difficulty breathing",
  "Stomach pain",
  "Broken bone / injury",
];

export default function TriagePage() {
  const router = useRouter();
  const [symptoms, setSymptoms] = useState("");
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [language, setLanguage] = useState("en");
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(
    null,
  );
  const [locStatus, setLocStatus] = useState<
    "idle" | "loading" | "got" | "error"
  >("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const getLocation = () => {
    setLocStatus("loading");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocStatus("got");
      },
      () => setLocStatus("error"),
      { timeout: 8000 },
    );
  };

  const handleSubmit = async () => {
    if (!symptoms.trim()) {
      setError("Please describe your symptoms.");
      return;
    }
    if (!location) {
      setError("Location is required to find nearby hospitals.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const result = await triageSymptoms({
        symptoms,
        latitude: location.lat,
        longitude: location.lng,
        language,
        radius_meters: 15000,
        age: age ? parseInt(age) : undefined,
        gender: gender || undefined,
      });
      sessionStorage.setItem("triageResult", JSON.stringify(result));
      router.push("/results");
    } catch (e: unknown) {
      setError(
        e instanceof Error
          ? e.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-background px-4 py-12 md:py-16">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className={`${mounted ? "fade-up" : ""} mb-12`}>
          <p className="text-xs font-bold uppercase tracking-widest text-primary mb-3">
            Step 1 of 3 · Symptom Assessment
          </p>
          <h1 className="font-bebas text-4xl md:text-6xl tracking-tight text-foreground mb-3">
            What Are You Feeling?
          </h1>
          <p className="text-sm md:text-base text-foreground-dim">
            Be as specific as possible — duration, intensity, and location of
            symptoms all help.
          </p>
        </div>

        {/* Quick select */}
        <div className={`${mounted ? "fade-up-delay-1" : ""} mb-6`}>
          <span className="label">Quick select</span>
          <div className="flex flex-wrap gap-2">
            {QUICK_SYMPTOMS.map((s) => (
              <button
                key={s}
                onClick={() =>
                  setSymptoms((prev) => (prev ? `${prev}, ${s}` : s))
                }
                className={`rounded-full px-4 py-2 text-xs font-medium transition-all duration-200 cursor-pointer ${
                  symptoms.includes(s)
                    ? "bg-primary/10 border-primary/30 border text-primary"
                    : "bg-surface border border-border text-foreground-dim hover:border-border-bright"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Symptom textarea */}
        <div className={`card mb-6 ${mounted ? "fade-up-delay-1" : ""} p-6`}>
          <span className="label">Describe your symptoms *</span>
          <textarea
            className="input-field resize-vertical"
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="e.g. I have a severe headache and fever since yesterday, along with neck stiffness and sensitivity to light..."
            rows={5}
          />
          <div className="mt-2 flex justify-end">
            <span
              className={`text-xs font-medium ${
                symptoms.length > 20 ? "text-primary" : "text-foreground-muted"
              }`}
            >
              {symptoms.length} chars{" "}
              {symptoms.length < 20 && symptoms.length > 0
                ? "— add more detail"
                : ""}
            </span>
          </div>
        </div>

        {/* Patient info */}
        <div className={`card mb-6 ${mounted ? "fade-up-delay-2" : ""} p-6`}>
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <span className="label">Age (optional)</span>
              <input
                type="number"
                className="input-field"
                placeholder="e.g. 34"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                min={1}
                max={120}
              />
            </div>
            <div>
              <span className="label">Gender (optional)</span>
              <select
                className="input-field appearance-none cursor-pointer"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
              >
                <option value="">Select</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div>
            <span className="label">Your language</span>
            <select
              className="input-field appearance-none cursor-pointer w-full"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Location */}
        <div className={`card mb-6 ${mounted ? "fade-up-delay-3" : ""} p-6`}>
          <span className="label">Your location *</span>
          <p className="mb-4 text-sm text-foreground-dim">
            Required to find hospitals near you.
          </p>
          <button
            onClick={getLocation}
            disabled={locStatus === "loading" || locStatus === "got"}
            className={`flex items-center gap-2 rounded-lg px-4 py-3 font-medium transition-all ${
              locStatus === "got"
                ? "cursor-default border border-severity-low/30 bg-severity-low/10 text-severity-low"
                : "btn-primary"
            }`}
          >
            {locStatus === "loading" && <div className="spinner" />}
            {locStatus === "got" && "✓"}
            {locStatus === "idle" && "📍"}
            {locStatus === "idle" && "Detect My Location"}
            {locStatus === "loading" && "Detecting..."}
            {locStatus === "got" &&
              `Location captured (${location?.lat.toFixed(3)}, ${location?.lng.toFixed(3)})`}
            {locStatus === "error" && "Retry Location"}
          </button>
          {locStatus === "error" && (
            <p className="mt-2 text-xs text-severity-high">
              Could not get location. Please enable location permissions and try
              again.
            </p>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-destructive/25 bg-destructive/8 px-4 py-3.5 text-sm text-destructive">
            ⚠ {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="btn-primary w-full justify-center text-base font-semibold py-3"
        >
          {loading ? (
            <>
              <div className="spinner" />
              Analyzing symptoms & finding hospitals...
            </>
          ) : (
            "Find Help Now →"
          )}
        </button>

        <p className="mt-3 text-center text-xs text-foreground-muted">
          🔒 Your data is private and not shared with third parties
        </p>
      </div>
    </div>
  );
}
