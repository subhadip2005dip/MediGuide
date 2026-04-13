"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  createBooking,
  type BookingRequest,
  type HospitalResult,
} from "@/lib/api";
import Link from "next/link";

export default function BookPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reportId = searchParams?.get("reportId");

  const [hospital, setHospital] = useState<HospitalResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    patientName: "",
    patientAge: "",
    patientGender: "male",
    patientBloodType: "",
    patientAllergies: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    emergencyContactEmail: "",
    appointmentDate: "",
    appointmentTime: "",
    ambulanceRequested: false,
  });

  useEffect(() => {
    const storedHospital = sessionStorage.getItem("selectedHospital");
    const storedTriage = sessionStorage.getItem("triageResult");

    if (storedHospital) {
      setHospital(JSON.parse(storedHospital));
    }

    if (storedTriage) {
      try {
        const triage = JSON.parse(storedTriage);
        if (triage.severity_score >= 8) {
          setFormData((prev) => ({ ...prev, ambulanceRequested: true }));
        }
      } catch (e) {
        console.error("Failed to parse triage", e);
      }
    }
  }, []);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >,
  ) => {
    const { name, value, type } = e.target;
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!hospital) {
      setError("No hospital selected. Please go back to results.");
      return;
    }

    if (
      !formData.patientName ||
      !formData.patientAge ||
      !formData.emergencyContactName ||
      !formData.emergencyContactPhone
    ) {
      setError("Please fill in all required fields.");
      return;
    }

    if (!formData.appointmentDate || !formData.appointmentTime) {
      setError("Please select appointment date and time.");
      return;
    }

    setLoading(true);

    try {
      const storedTriage = sessionStorage.getItem("triageResult");
      let symptoms = "";
      let severityScore = 5;
      let recommendedSpecialty = "General Physician";

      if (storedTriage) {
        const triage = JSON.parse(storedTriage);
        symptoms = triage.ai_summary || "";
        severityScore = triage.severity_score || 5;
        recommendedSpecialty =
          triage.recommended_specialty || "General Physician";
      }

      const appointmentDateTime = new Date(
        `${formData.appointmentDate}T${formData.appointmentTime}`,
      ).toISOString();

      const bookingData: BookingRequest = {
        symptom_report_id: reportId ? parseInt(reportId) : undefined,
        hospital_place_id: hospital.place_id,
        hospital_name: hospital.name,
        hospital_address: hospital.address,
        hospital_phone: hospital.phone || undefined,
        patient_name: formData.patientName,
        patient_age: parseInt(formData.patientAge),
        patient_gender: formData.patientGender,
        patient_blood_type: formData.patientBloodType || undefined,
        patient_allergies: formData.patientAllergies || undefined,
        emergency_contact_name: formData.emergencyContactName,
        emergency_contact_phone: formData.emergencyContactPhone,
        emergency_contact_email: formData.emergencyContactEmail || undefined,
        appointment_time: appointmentDateTime,
        ambulance_requested: formData.ambulanceRequested,
        symptoms,
        severity_score: severityScore,
        recommended_specialty: recommendedSpecialty,
      };

      const response = await createBooking(bookingData);

      sessionStorage.setItem("bookingConfirmation", JSON.stringify(response));
      router.push(`/confirmation?bookingId=${response.booking_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Booking failed");
      setLoading(false);
    }
  };

  if (!hospital) {
    return (
      <div className="min-h-screen bg-background px-8 py-8">
        <div className="mx-auto max-w-md text-center">
          <h1 className="text-3xl text-foreground mb-4">
            No Hospital Selected
          </h1>
          <p className="text-foreground-dim mb-8">
            Please select a hospital from the results page first.
          </p>
          <Link href="/triage" className="btn-primary">
            Back to Triage
          </Link>
        </div>
      </div>
    );
  }

  const todayDate = new Date().toISOString().split("T")[0];
  const minTime = "08:00";
  const maxTime = "20:00";

  return (
    <div className="min-h-screen bg-background px-8 py-8">
      <div className="mx-auto max-w-3xl">
        <div className="mb-8">
          <Link href="/results" className="text-primary no-underline text-sm">
            ← Back to Results
          </Link>
        </div>

        <h1 className="text-4xl text-foreground font-bebas mb-1 tracking-wide">
          Book Appointment
        </h1>

        <div className="card mb-8 p-6">
          <h3 className="text-xl text-primary mb-1 font-semibold">
            {hospital.name}
          </h3>
          <p className="text-foreground-dim text-sm mb-1">
            📍 {hospital.address}
          </p>
          {hospital.phone && (
            <p className="text-foreground-dim text-sm">📞 {hospital.phone}</p>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="card p-8 mb-8">
            <h2 className="text-2xl text-foreground font-bebas mb-6 tracking-wide">
              Patient Information
            </h2>

            <div className="grid gap-6">
              <div>
                <label
                  htmlFor="patientName"
                  className="block text-foreground text-sm mb-2"
                >
                  Full Name *
                </label>
                <input
                  type="text"
                  id="patientName"
                  name="patientName"
                  value={formData.patientName}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="patientAge"
                    className="block text-foreground text-sm mb-2"
                  >
                    Age *
                  </label>
                  <input
                    type="number"
                    id="patientAge"
                    name="patientAge"
                    value={formData.patientAge}
                    onChange={handleInputChange}
                    min="0"
                    max="120"
                    required
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                  />
                </div>

                <div>
                  <label
                    htmlFor="patientGender"
                    className="block text-foreground text-sm mb-2"
                  >
                    Gender *
                  </label>
                  <select
                    id="patientGender"
                    name="patientGender"
                    value={formData.patientGender}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="patientBloodType"
                    className="block text-foreground text-sm mb-2"
                  >
                    Blood Type
                  </label>
                  <input
                    type="text"
                    id="patientBloodType"
                    name="patientBloodType"
                    value={formData.patientBloodType}
                    onChange={handleInputChange}
                    placeholder="e.g., A+, O-"
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                  />
                </div>

                <div>
                  <label
                    htmlFor="patientAllergies"
                    className="block text-foreground text-sm mb-2"
                  >
                    Allergies
                  </label>
                  <input
                    type="text"
                    id="patientAllergies"
                    name="patientAllergies"
                    value={formData.patientAllergies}
                    onChange={handleInputChange}
                    placeholder="e.g., Penicillin"
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                  />
                </div>
              </div>
            </div>

            <h2 className="text-2xl text-foreground font-bebas mt-8 mb-6 tracking-wide">
              Emergency Contact
            </h2>

            <div className="grid gap-6">
              <div>
                <label
                  htmlFor="emergencyContactName"
                  className="block text-foreground text-sm mb-2"
                >
                  Contact Name *
                </label>
                <input
                  type="text"
                  id="emergencyContactName"
                  name="emergencyContactName"
                  value={formData.emergencyContactName}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="emergencyContactPhone"
                    className="block text-foreground text-sm mb-2"
                  >
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    id="emergencyContactPhone"
                    name="emergencyContactPhone"
                    value={formData.emergencyContactPhone}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                  />
                </div>

                <div>
                  <label
                    htmlFor="emergencyContactEmail"
                    className="block text-foreground text-sm mb-2"
                  >
                    Email
                  </label>
                  <input
                    type="email"
                    id="emergencyContactEmail"
                    name="emergencyContactEmail"
                    value={formData.emergencyContactEmail}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                  />
                </div>
              </div>
            </div>

            <h2 className="text-2xl text-foreground font-bebas mt-8 mb-6 tracking-wide">
              Appointment Details
            </h2>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label
                  htmlFor="appointmentDate"
                  className="block text-foreground text-sm mb-2"
                >
                  Date *
                </label>
                <input
                  type="date"
                  id="appointmentDate"
                  name="appointmentDate"
                  value={formData.appointmentDate}
                  onChange={handleInputChange}
                  min={todayDate}
                  required
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                />
              </div>

              <div>
                <label
                  htmlFor="appointmentTime"
                  className="block text-foreground text-sm mb-2"
                >
                  Time *
                </label>
                <input
                  type="time"
                  id="appointmentTime"
                  name="appointmentTime"
                  value={formData.appointmentTime}
                  onChange={handleInputChange}
                  min={minTime}
                  max={maxTime}
                  required
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground text-base"
                />
              </div>
            </div>

            <div
              className={`p-4 rounded-lg border flex items-center gap-4 ${
                formData.ambulanceRequested
                  ? "bg-destructive/10 border-destructive/30"
                  : "bg-primary/5 border-border"
              }`}
            >
              <input
                type="checkbox"
                id="ambulanceRequested"
                name="ambulanceRequested"
                checked={formData.ambulanceRequested}
                onChange={handleInputChange}
                className="w-5 h-5 cursor-pointer"
              />
              <label
                htmlFor="ambulanceRequested"
                className="text-foreground text-base cursor-pointer flex-1"
              >
                {formData.ambulanceRequested ? "🚨 " : ""}Request Ambulance
                Transportation
                {formData.ambulanceRequested && (
                  <span className="block text-xs text-foreground-dim mt-1">
                    Additional $300 fee applies
                  </span>
                )}
              </label>
            </div>

            {error && (
              <div className="mt-6 p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-8 text-lg font-bebas tracking-wide"
              style={{
                opacity: loading ? 0.6 : 1,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Confirming Booking..." : "Confirm Booking"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
