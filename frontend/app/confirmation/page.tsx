"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { generateFamilyReport, type BookingResponse } from "@/lib/api";
import Link from "next/link";

export default function ConfirmationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingId = searchParams?.get("bookingId");

  const [booking, setBooking] = useState<BookingResponse | null>(null);
  const [familyReport, setFamilyReport] = useState<string | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [reportError, setReportError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const storedBooking = sessionStorage.getItem("bookingConfirmation");
    if (storedBooking) {
      setBooking(JSON.parse(storedBooking));
    }
  }, []);

  const handleGenerateReport = async () => {
    if (!bookingId) {
      setReportError("No booking ID found");
      return;
    }

    setLoadingReport(true);
    setReportError("");

    try {
      const response = await generateFamilyReport(parseInt(bookingId));
      setFamilyReport(response.family_report_text);
    } catch (err) {
      setReportError(
        err instanceof Error ? err.message : "Failed to generate report",
      );
    } finally {
      setLoadingReport(false);
    }
  };

  const handleCopyReport = () => {
    if (familyReport) {
      navigator.clipboard.writeText(familyReport);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleWhatsAppShare = () => {
    if (familyReport) {
      const encodedText = encodeURIComponent(familyReport);
      window.open(`https://wa.me/?text=${encodedText}`, "_blank");
    }
  };

  if (!booking) {
    return (
      <div className="min-h-screen bg-background px-4 py-8">
        <div className="mx-auto max-w-md text-center">
          <h1 className="mb-3 text-3xl font-bold text-foreground">
            No Booking Found
          </h1>
          <p className="mb-6 text-foreground-dim">
            Please complete a booking first.
          </p>
          <Link href="/triage" className="btn-primary">
            Start New Triage
          </Link>
        </div>
      </div>
    );
  }

  const appointmentDate = new Date(booking.appointment_time);
  const formattedDate = appointmentDate.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = appointmentDate.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-12 border-b border-border pb-8 text-center">
          <div className="mb-4 text-5xl">✅</div>
          <h1 className="mb-2 font-bebas text-4xl tracking-wide text-primary">
            Booking Confirmed
          </h1>
          <p className="text-lg text-foreground-dim">
            Your appointment has been successfully scheduled
          </p>
        </div>

        {/* Appointment Details Card */}
        <div className="card mb-8 p-8">
          <h2 className="mb-6 font-bebas text-2xl tracking-wide text-foreground">
            Appointment Details
          </h2>

          <div className="space-y-6">
            <div>
              <div className="text-xs text-foreground-dim mb-1">Patient</div>
              <div className="text-base text-foreground font-medium">
                {booking.patient_name}
              </div>
            </div>

            <div>
              <div className="text-xs text-foreground-dim mb-1">Hospital</div>
              <div className="text-base text-foreground font-medium">
                {booking.hospital_name}
              </div>
              <div className="text-sm text-foreground-dim mt-1">
                📍 {booking.hospital_address}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="text-xs text-foreground-dim mb-1">Date</div>
                <div className="text-base text-foreground">{formattedDate}</div>
              </div>

              <div>
                <div className="text-xs text-foreground-dim mb-1">Time</div>
                <div className="text-base text-foreground">{formattedTime}</div>
              </div>
            </div>

            {booking.ambulance_requested && (
              <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg flex items-center gap-3">
                <span className="text-2xl">🚨</span>
                <div>
                  <div className="text-destructive font-semibold mb-1">
                    Ambulance Requested
                  </div>
                  <div className="text-xs text-foreground-dim">
                    Emergency transportation has been dispatched
                  </div>
                </div>
              </div>
            )}

            <div>
              <div className="text-xs text-foreground-dim mb-1">
                Estimated Cost
              </div>
              <div className="text-2xl text-primary font-semibold">
                ${booking.estimated_cost_usd} USD
              </div>
              <div className="text-xs text-foreground-muted mt-1">
                This is an estimate. Actual costs may vary based on treatment.
              </div>
            </div>

            <div>
              <div className="text-xs text-foreground-dim mb-2">
                Booking Status
              </div>
              <div className="inline-block px-4 py-2 bg-primary/15 border border-primary/30 rounded text-sm text-primary font-semibold uppercase tracking-wider">
                {booking.status}
              </div>
            </div>
          </div>
        </div>

        {!familyReport ? (
          <div className="card mb-8 p-8">
            <h2 className="text-2xl text-foreground font-bebas mb-4 tracking-wide">
              Family Report
            </h2>
            <p className="text-foreground-dim mb-6 leading-relaxed">
              Generate a plain-language medical summary to share with your
              family members. This report explains the situation in simple terms
              they can understand.
            </p>

            {reportError && (
              <div className="mb-6 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive">
                {reportError}
              </div>
            )}

            <button
              onClick={handleGenerateReport}
              disabled={loadingReport}
              className="btn-primary"
              style={{
                opacity: loadingReport ? 0.6 : 1,
                cursor: loadingReport ? "not-allowed" : "pointer",
              }}
            >
              {loadingReport
                ? "Generating Report..."
                : "Generate Family Report"}
            </button>
          </div>
        ) : (
          <div className="card mb-8 p-8">
            <h2 className="text-2xl text-foreground font-bebas mb-6 tracking-wide">
              Family Report
            </h2>

            <div className="p-6 bg-surface border border-border rounded-lg mb-6 whitespace-pre-wrap leading-relaxed text-foreground text-sm">
              {familyReport}
            </div>

            <div className="flex gap-4 flex-wrap">
              <button
                onClick={handleCopyReport}
                className={`px-6 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  copied
                    ? "bg-primary/15 border border-primary/30 text-primary"
                    : "bg-surface border border-border text-foreground"
                }`}
              >
                {copied ? "✓ Copied!" : "📋 Copy to Clipboard"}
              </button>

              <button
                onClick={handleWhatsAppShare}
                className="px-6 py-2 bg-[#25D366] border border-[#1da851] rounded-lg text-white text-sm font-medium transition-all cursor-pointer"
              >
                📱 Share via WhatsApp
              </button>
            </div>
          </div>
        )}

        <div className="text-center">
          <Link
            href="/"
            className="btn-secondary inline-block px-8 py-3 bg-surface border border-border rounded-lg text-foreground text-base font-medium transition-all"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
