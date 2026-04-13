"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { TriageResponse, HospitalResult } from "@/lib/api";

const SEVERITY_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; border: string; icon: string }
> = {
  low: {
    label: "LOW",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.08)",
    border: "rgba(34,197,94,0.2)",
    icon: "✓",
  },
  medium: {
    label: "MEDIUM",
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.08)",
    border: "rgba(245,158,11,0.2)",
    icon: "!",
  },
  high: {
    label: "HIGH",
    color: "#f97316",
    bg: "rgba(249,115,22,0.08)",
    border: "rgba(249,115,22,0.2)",
    icon: "!!",
  },
  emergency: {
    label: "EMERGENCY",
    color: "#ef4444",
    bg: "rgba(239,68,68,0.1)",
    border: "rgba(239,68,68,0.3)",
    icon: "🚨",
  },
};

function StarRating({ rating }: { rating: number }) {
  return (
    <span className="text-yellow-500 text-xs">
      {"★".repeat(Math.round(rating))}
      {"☆".repeat(5 - Math.round(rating))}
      <span className="text-foreground-muted ml-1">{rating.toFixed(1)}</span>
    </span>
  );
}

function HospitalCard({
  hospital,
  rank,
  reportId,
}: {
  hospital: HospitalResult;
  rank: number;
  reportId: number;
}) {
  const router = useRouter();
  const isFirst = rank === 1;

  const handleBook = () => {
    sessionStorage.setItem("selectedHospital", JSON.stringify(hospital));
    router.push(`/book?reportId=${reportId}`);
  };

  return (
    <div
      className={`card card-hover p-6 ${isFirst ? "border border-primary/30" : "border border-border"} relative overflow-hidden`}
    >
      {isFirst && (
        <div className="absolute top-4 right-4 bg-primary/12 border border-primary/25 text-primary text-xs font-bold tracking-widest px-2 py-1 rounded-full">
          BEST MATCH
        </div>
      )}

      <div className="flex items-start gap-4">
        {/* Rank */}
        <div
          className={`font-bebas text-3xl ${isFirst ? "text-primary" : "text-foreground-muted"} leading-none min-w-max`}
        >
          #{rank}
        </div>

        <div className="flex-1">
          <h3 className="text-base font-semibold text-foreground mb-1">
            {hospital.name}
          </h3>
          <p className="text-foreground-muted text-xs mb-2">
            📍 {hospital.address}
          </p>

          <div className="flex flex-wrap gap-3 mb-3 items-center">
            {hospital.rating && <StarRating rating={hospital.rating} />}
            <span className="text-foreground-dim text-xs">
              🗺 {hospital.distance_km} km
            </span>
            {hospital.open_now === true && (
              <span className="text-green-500 text-xs font-semibold">
                ● Open Now
              </span>
            )}
            {hospital.open_now === false && (
              <span className="text-destructive text-xs">● Closed</span>
            )}
          </div>

          <p className="text-xs text-foreground-muted bg-surface rounded px-3 py-1 mb-4">
            {hospital.match_reason}
          </p>

          <div className="flex gap-3 flex-wrap">
            <button
              onClick={handleBook}
              className="btn-primary py-1.5 px-5 text-sm"
            >
              Book Appointment →
            </button>
            <a
              href={hospital.google_maps_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <button className="btn-ghost py-1.5 px-4 text-xs">
                View on Maps ↗
              </button>
            </a>
            {hospital.phone && (
              <a href={`tel:${hospital.phone}`}>
                <button className="btn-ghost py-1.5 px-4 text-xs">
                  📞 Call
                </button>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResultsPage() {
  const [result, setResult] = useState<TriageResponse | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = sessionStorage.getItem("triageResult");
    if (stored) setResult(JSON.parse(stored));
  }, []);

  if (!result) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center flex-col gap-4">
        <div
          className="spinner"
          style={{ width: 36, height: 36, borderWidth: 3 }}
        />
        <p className="text-foreground-muted">Loading results...</p>
        {mounted && (
          <Link href="/triage">
            <button className="btn-ghost mt-4">← Start New Assessment</button>
          </Link>
        )}
      </div>
    );
  }

  const sev = SEVERITY_CONFIG[result.severity] || SEVERITY_CONFIG.medium;
  const isEmergency = result.severity === "emergency";

  return (
    <div className="min-h-[calc(100vh-64px)] bg-background px-6 py-10">
      <div className="mx-auto max-w-2xl">
        <div
          className={`${mounted ? "fade-up" : ""} ${isEmergency ? "pulse-emergency" : ""} rounded-2xl p-6 mb-6`}
          style={{
            background: sev.bg,
            border: `1px solid ${sev.border}`,
          }}
        >
          <div className="flex items-center gap-4 mb-3">
            <div
              className="font-bebas text-5xl leading-none"
              style={{ color: sev.color }}
            >
              {result.severity_score}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="font-bold text-xs tracking-widest"
                  style={{ color: sev.color }}
                >
                  SEVERITY — {sev.label}
                </span>
                {isEmergency && <span className="text-xl">🚨</span>}
              </div>
              <p
                className="text-sm mt-1"
                style={{ color: "var(--foreground-dim)" }}
              >
                {result.escalation_message}
              </p>
            </div>
          </div>

          {isEmergency && (
            <a href="tel:112">
              <button
                className="btn-primary text-lg py-2 px-8"
                style={{
                  background: "#ef4444",
                }}
              >
                📞 Call Emergency — 112
              </button>
            </a>
          )}
        </div>

        <div className={`card ${mounted ? "fade-up-delay-1" : ""} p-6 mb-6`}>
          <div className="flex justify-between items-start mb-4 flex-wrap gap-2">
            <h2 className="text-base font-semibold text-foreground">
              AI Assessment
            </h2>
            <div className="flex gap-2 flex-wrap">
              <span className="bg-primary/8 border border-primary/20 text-primary text-xs px-2 py-1 rounded-full font-semibold">
                {result.recommended_specialty}
              </span>
              <span className="bg-surface border border-border text-foreground-dim text-xs px-2 py-1 rounded-full">
                {result.estimated_visit_type}
              </span>
            </div>
          </div>

          <p className="text-foreground leading-relaxed mb-4">
            {result.ai_summary}
          </p>

          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs text-foreground-muted whitespace-nowrap">
              Confidence
            </span>
            <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000"
                style={{
                  width: `${result.confidence_score * 100}%`,
                  background:
                    result.confidence_score > 0.7
                      ? "var(--primary)"
                      : "#f59e0b",
                }}
              />
            </div>
            <span className="text-xs text-primary font-semibold whitespace-nowrap">
              {Math.round(result.confidence_score * 100)}%
            </span>
          </div>

          {result.red_flags.length > 0 && (
            <div className="bg-destructive/7 border border-destructive/20 rounded-lg p-3.5">
              <p className="text-destructive text-xs font-bold tracking-wider mb-2">
                ⚠ RED FLAGS DETECTED
              </p>
              {result.red_flags.map((flag) => (
                <p key={flag} className="text-foreground-dim text-xs">
                  • {flag}
                </p>
              ))}
            </div>
          )}
        </div>

        <div className={`card ${mounted ? "fade-up-delay-2" : ""} p-6 mb-6`}>
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-base font-semibold text-foreground">
              Doctor Card
              <span className="text-foreground-muted font-normal text-xs ml-2">
                {" "}
                — show this to your doctor
              </span>
            </h2>
            <button
              onClick={() =>
                navigator.clipboard?.writeText(result.symptom_card)
              }
              className="border border-border text-foreground-muted px-3 py-0.5 rounded text-xs cursor-pointer hover:bg-surface transition-colors"
            >
              Copy
            </button>
          </div>
          <div className="bg-surface rounded-lg p-4 text-foreground leading-relaxed text-sm border-l-4 border-primary">
            {result.symptom_card}
          </div>
        </div>

        {/* Pharmacy Option for Low Severity */}
        {result.severity === "low" && (
          <div
            className={`card ${mounted ? "fade-up-delay-2" : ""} p-6 mb-6 bg-green-500/5 border border-green-500/20`}
          >
            <div className="flex items-start gap-4">
              <div className="text-2xl min-w-max">💊</div>
              <div className="flex-1">
                <h3 className="text-base font-semibold text-foreground mb-2">
                  No Doctor Visit Needed
                </h3>
                <p className="text-foreground-dim text-sm mb-4 leading-relaxed">
                  Based on your assessment, you don't need to visit a doctor
                  right now. If you need any over-the-counter medications, you
                  can visit a nearby pharmacy to get what you need.
                </p>
                <Link href="/pharmacy">
                  <button className="btn-primary bg-green-500 text-white py-1.5 px-6 text-sm">
                    Find Nearby Pharmacies →
                  </button>
                </Link>
              </div>
            </div>
          </div>
        )}

        <div className={mounted ? "fade-up-delay-3" : ""}>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-foreground">
              Nearby Hospitals
            </h2>
            <span className="text-foreground-muted text-xs">
              {result.total_hospitals_found} found · showing top{" "}
              {result.hospitals.length}
            </span>
          </div>

          <div className="space-y-4">
            {result.hospitals.map((h, i) => (
              <HospitalCard
                key={h.place_id}
                hospital={h}
                rank={i + 1}
                reportId={result.report_id}
              />
            ))}
          </div>
        </div>

        <div className="text-center mt-10">
          <Link href="/triage">
            <button className="btn-ghost">← Start New Assessment</button>
          </Link>
        </div>
      </div>
    </div>
  );
}
