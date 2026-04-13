const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TriageRequest {
  symptoms: string;
  latitude: number;
  longitude: number;
  language?: string;
  radius_meters?: number;
  age?: number;
  gender?: string;
}

export interface HospitalResult {
  place_id: string;
  name: string;
  address: string;
  phone: string | null;
  rating: number | null;
  user_ratings_total?: number | null;
  distance_km: number;
  open_now: boolean | null;
  match_score: number;
  match_reason: string;
  google_maps_url: string;
}

export interface PharmacyResult {
  place_id: string;
  name: string;
  address: string;
  phone: string | null;
  rating: number | null;
  distance_km: number;
  open_now: boolean | null;
  google_maps_url: string;
}

export interface TriageResponse {
  report_id: number;
  severity: string;
  severity_score: number;
  severity_color: string;
  urgency_label: string;
  recommended_specialty: string;
  ai_summary: string;
  action_advice: string;
  symptom_card: string;
  confidence_score: number;
  confidence_reason: string;
  red_flags: string[];
  estimated_visit_type: string;
  escalation_action: string;
  escalation_message: string;
  hospitals: HospitalResult[];
  emergency_call_advised: boolean;
  total_hospitals_found: number;
  pharmacies: PharmacyResult[];
  show_pharmacies: boolean;
}

export interface BookingRequest {
  symptom_report_id?: number;
  user_id?: number;
  hospital_place_id: string;
  hospital_name: string;
  hospital_address: string;
  hospital_phone?: string;
  patient_name: string;
  patient_age: number;
  patient_gender: string;
  patient_blood_type?: string;
  patient_allergies?: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_email?: string;
  appointment_time: string;
  ambulance_requested?: boolean;
  symptoms?: string;
  severity_score?: number;
  recommended_specialty?: string;
}

export interface BookingResponse {
  booking_id: number;
  status: string;
  hospital_name: string;
  hospital_address: string;
  hospital_phone: string | null;
  appointment_time: string;
  patient_name: string;
  ambulance_requested: boolean;
  cost_tier: string;
  cost_tier_label: string;
  cost_tier_note: string;
  consultation_range_inr: string;
  tests_range_inr: string;
  medicines_range_inr: string;
  total_range_inr: string;
  ambulance_cost: string | null;
  cost_severity_note: string;
  intake_note: string;
  created_at: string;
}

export interface FamilyReportResponse {
  booking_id: number;
  family_report_text: string;
  generated_at: string;
}

export async function triageSymptoms(
  data: TriageRequest,
): Promise<TriageResponse> {
  const res = await fetch(`${API_URL}/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Triage failed");
  }
  return res.json();
}

export async function createBooking(
  data: BookingRequest,
): Promise<BookingResponse> {
  const res = await fetch(`${API_URL}/bookings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Booking failed");
  }
  return res.json();
}

export async function generateFamilyReport(
  bookingId: number,
): Promise<FamilyReportResponse> {
  const res = await fetch(`${API_URL}/bookings/${bookingId}/family-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Report generation failed");
  }
  return res.json();
}
