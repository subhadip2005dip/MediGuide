"use client";

import { useState, useEffect, useRef } from "react";
import { recordAndTranslate } from "@/hooks/useVoiceTranslate";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Mic,
  Stethoscope,
  User,
  Languages,
  Volume2,
  AlertCircle,
  Music,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const GOOGLE_TTS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_CLOUD_TTS_API_KEY;

interface Language {
  code: string;
  name: string;
  tts_lang: string;
}

export default function InterpreterPage() {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [conversation, setConversation] = useState<any[]>([]);
  const [patientLang, setPatientLang] = useState("hi");
  const [doctorLang, setDoctorLang] = useState("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeSpeaker, setActiveSpeaker] = useState<
    "patient" | "doctor" | null
  >(null);
  const [playing, setPlaying] = useState<string | null>(null);
  const [autoPlay, setAutoPlay] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const autoPlayedEntriesRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    fetch(`${API_URL}/translate/languages`)
      .then((r) => r.json())
      .then((d) => setLanguages(d.languages))
      .catch((err) => {
        console.error("Failed to load languages:", err);
        setError("Could not connect to medical translation service.");
      });
  }, []);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation]);

  async function playTTS(text: string, lang: string, entryId: string) {
    if (!GOOGLE_TTS_API_KEY) {
      setError("Google Cloud TTS API key not configured");
      return;
    }

    try {
      setPlaying(entryId);

      const googleTtsLangMap: Record<string, string> = {
        en: "en-US",
        hi: "hi-IN",
      };

      const googleTtsLang = googleTtsLangMap[lang] || "en-US";

      const voiceMap: Record<string, { languageCode: string; name: string }> = {
        "en-US": { languageCode: "en-US", name: "en-US-Neural2-C" },
        "hi-IN": { languageCode: "hi-IN", name: "hi-IN-Neural2-C" },
      };

      const voice = voiceMap[googleTtsLang] || voiceMap["en-US"];

      console.log(
        `TTS Request: language=${googleTtsLang}, voice=${voice.name}, text="${text.substring(0, 50)}..."`,
      );

      const response = await fetch(
        `https://texttospeech.googleapis.com/v1/text:synthesize?key=${GOOGLE_TTS_API_KEY}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            input: { text },
            voice: {
              languageCode: voice.languageCode,
              name: voice.name,
            },
            audioConfig: {
              audioEncoding: "MP3",
              pitch: 2,
              speakingRate: 1.0,
              volumeGainDb: 2,
            },
          }),
        },
      );

      console.log(
        `TTS Response Status: ${response.status} ${response.statusText}`,
      );

      if (!response.ok) {
        let errorDetails = `HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorDetails =
            errorData.error?.message || errorData.message || errorDetails;
        } catch (e) {}
        console.error(
          `Google Cloud TTS API Error: ${errorDetails}`,
          `Language: ${googleTtsLang}, Voice: ${voice.name}, Key: ${GOOGLE_TTS_API_KEY?.substring(0, 10)}...`,
        );
        setPlaying(null);
        setError(
          `TTS Error: ${errorDetails}. Make sure Text-to-Speech API is enabled in Google Cloud Console.`,
        );
        return;
      }

      const audioData = await response.json();

      if (!audioData.audioContent) {
        console.error(
          "Google Cloud TTS response missing audioContent:",
          audioData,
        );
        setPlaying(null);
        setError("TTS failed: No audio data received");
        return;
      }

      console.log("TTS Audio received, converting to blob...");

      const audioBlob = new Blob(
        [Uint8Array.from(atob(audioData.audioContent), (c) => c.charCodeAt(0))],
        { type: "audio/mpeg" },
      );
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setPlaying(null);
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
      console.log("TTS playback started");
    } catch (err) {
      console.error("TTS playback error:", err);
      setPlaying(null);
      setError(
        `Audio playback failed: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
    }
  }

  useEffect(() => {
    if (autoPlay && conversation.length > 0) {
      const lastEntry = conversation[conversation.length - 1];
      if (
        lastEntry &&
        !autoPlayedEntriesRef.current.has(lastEntry.id) &&
        !playing
      ) {
        playTTS(lastEntry.translated, lastEntry.tts_lang, lastEntry.id);
        autoPlayedEntriesRef.current.add(lastEntry.id);
      }
    }
  }, [conversation, autoPlay, playing]);

  const handleSpeak = async (speaker: "patient" | "doctor") => {
    setLoading(true);
    setActiveSpeaker(speaker);
    setError("");

    try {
      await recordAndTranslate({
        speaker,
        patientLang,
        doctorLang,
        API_URL,
        speak: (text: string, lang: string) => {},
        onResult: (data: any) => {
          setConversation((prev) => [...prev, data]);
          setLoading(false);
          setActiveSpeaker(null);
        },
      });
    } catch (err: any) {
      console.error("Recording error:", err);
      setError(
        err.message ||
          "Recording failed. Please ensure microphone access is granted.",
      );
      setLoading(false);
      setActiveSpeaker(null);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-background overflow-x-hidden">
      <main className="relative container mx-auto max-w-5xl px-4 py-8 md:py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <Badge
            variant="outline"
            className="border-primary/20 bg-primary/5 text-primary mb-4 inline-flex"
          >
            <Languages className="mr-2 h-4 w-4" />
            <span className="text-xs font-semibold tracking-wider uppercase">
              Live Translation
            </span>
          </Badge>
          <h1 className="mb-3 font-bebas text-5xl md:text-7xl tracking-tight text-foreground">
            Clinical <span className="text-primary">Interpreter</span>
          </h1>
          <p className="mx-auto max-w-2xl text-sm md:text-base text-foreground-dim leading-relaxed">
            Real-time medical translation between patient and clinical staff.
            Speak naturally—we handle the language barrier.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-10 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6"
        >
          <div className="rounded-2xl border border-border/50 bg-card/30 backdrop-blur p-6">
            <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-foreground-muted mb-4">
              <User className="h-4 w-4 text-primary" />
              Patient Language
            </label>
            <select
              value={patientLang}
              onChange={(e) => setPatientLang(e.target.value)}
              disabled={loading}
              className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-foreground text-sm font-medium transition-colors hover:border-border-bright focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 disabled:opacity-50"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <div className="rounded-2xl border border-border/50 bg-card/30 backdrop-blur p-6">
            <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-foreground-muted mb-4">
              <Stethoscope className="h-4 w-4 text-severity-low" />
              Doctor Language
            </label>
            <select
              value={doctorLang}
              onChange={(e) => setDoctorLang(e.target.value)}
              disabled={loading}
              className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-foreground text-sm font-medium transition-colors hover:border-border-bright focus:outline-none focus:border-severity-low focus:ring-1 focus:ring-severity-low/30 disabled:opacity-50"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-10 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6"
        >
          <Button
            size="lg"
            onClick={() => handleSpeak("patient")}
            disabled={loading}
            className={`group relative h-32 overflow-hidden rounded-2xl border-2 transition-all duration-300 ${
              activeSpeaker === "patient"
                ? "border-primary bg-primary text-black shadow-lg shadow-primary/30"
                : "border-primary/30 bg-primary/5 text-primary hover:bg-primary/10 hover:border-primary/50"
            }`}
          >
            <div className="relative z-10 flex flex-col items-center justify-center gap-3 h-full">
              <AnimatePresence mode="wait">
                {activeSpeaker === "patient" ? (
                  <motion.div
                    key="loading"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="flex gap-1.5"
                  >
                    <span className="h-2 w-2 rounded-full bg-black animate-bounce [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 rounded-full bg-black animate-bounce [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 rounded-full bg-black animate-bounce" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="icon"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                  >
                    <Mic className="h-8 w-8 group-hover:scale-110 transition-transform" />
                  </motion.div>
                )}
              </AnimatePresence>
              <span className="font-semibold text-sm tracking-wider uppercase">
                Patient Voice
              </span>
            </div>
          </Button>

          <Button
            size="lg"
            onClick={() => handleSpeak("doctor")}
            disabled={loading}
            className={`group relative h-32 overflow-hidden rounded-2xl border-2 transition-all duration-300 ${
              activeSpeaker === "doctor"
                ? "border-severity-low bg-severity-low text-black shadow-lg shadow-severity-low/30"
                : "border-severity-low/30 bg-severity-low/5 text-severity-low hover:bg-severity-low/10 hover:border-severity-low/50"
            }`}
          >
            <div className="relative z-10 flex flex-col items-center justify-center gap-3 h-full">
              <AnimatePresence mode="wait">
                {activeSpeaker === "doctor" ? (
                  <motion.div
                    key="loading"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="flex gap-1.5"
                  >
                    <span className="h-2 w-2 rounded-full bg-black animate-bounce [animation-delay:-0.3s]" />
                    <span className="h-2 w-2 rounded-full bg-black animate-bounce [animation-delay:-0.15s]" />
                    <span className="h-2 w-2 rounded-full bg-black animate-bounce" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="icon"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                  >
                    <Stethoscope className="h-8 w-8 group-hover:scale-110 transition-transform" />
                  </motion.div>
                )}
              </AnimatePresence>
              <span className="font-semibold text-sm tracking-wider uppercase">
                Doctor Voice
              </span>
            </div>
          </Button>
        </motion.div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-8 flex items-center gap-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
            >
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>{error}</p>
              <button
                onClick={() => setError("")}
                className="ml-auto text-destructive/60 hover:text-destructive transition-colors"
              >
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Auto-play Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-6 flex items-center justify-between rounded-lg border border-border/50 bg-card/30 px-4 py-3 backdrop-blur"
        >
          <div className="flex items-center gap-2">
            <Music className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold uppercase tracking-wider text-foreground-muted">
              Auto-play Translations
            </span>
          </div>
          <button
            onClick={() => setAutoPlay(!autoPlay)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              autoPlay ? "bg-primary" : "bg-border"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                autoPlay ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </motion.div>

        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-foreground-muted mb-4 px-2">
            Conversation History
          </h2>

          <Card className="flex flex-col overflow-hidden border-border bg-card/30 backdrop-blur rounded-2xl">
            <div className="flex-1 overflow-y-auto px-4 py-8 md:px-6 space-y-8 min-h-100">
              {conversation.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center opacity-50 py-16">
                  <Mic className="h-10 w-10 text-foreground-muted mb-4" />
                  <p className="text-sm text-foreground-muted">
                    No recordings yet. Click a button to start.
                  </p>
                </div>
              ) : (
                <>
                  {conversation.map((entry) => (
                    <motion.div
                      key={entry.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex w-full flex-col gap-3 ${
                        entry.speaker === "patient"
                          ? "items-start"
                          : "items-end"
                      }`}
                    >
                      <div
                        className={`flex items-center gap-2 text-xs font-semibold uppercase tracking-wider ${
                          entry.speaker === "patient"
                            ? "text-primary"
                            : "text-severity-low"
                        }`}
                      >
                        {entry.speaker === "patient" ? (
                          <User className="h-4 w-4" />
                        ) : (
                          <Stethoscope className="h-4 w-4" />
                        )}
                        {entry.speaker === "patient" ? "Patient" : "Doctor"}
                      </div>

                      <div
                        className={`w-full max-w-md rounded-xl px-4 py-3 ${
                          entry.speaker === "patient"
                            ? "rounded-tl-none bg-primary/10 text-foreground"
                            : "rounded-tr-none bg-foreground/5 text-foreground"
                        }`}
                      >
                        <p className="text-sm leading-relaxed">
                          {entry.original}
                        </p>
                      </div>

                      <div
                        className={`w-full max-w-md rounded-xl px-4 py-3 border-2 ${
                          entry.speaker === "patient"
                            ? "rounded-tl-none border-primary/30 bg-primary/5"
                            : "rounded-tr-none border-severity-low/30 bg-severity-low/5"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <p
                              className={`text-sm font-semibold ${
                                entry.speaker === "patient"
                                  ? "text-primary"
                                  : "text-severity-low"
                              }`}
                            >
                              {entry.translated}
                            </p>
                          </div>
                          <button
                            onClick={() =>
                              playTTS(
                                entry.translated,
                                entry.tts_lang,
                                entry.id,
                              )
                            }
                            disabled={playing === entry.id}
                            className={`shrink-0 p-1.5 rounded-lg transition-all ${
                              playing === entry.id
                                ? entry.speaker === "patient"
                                  ? "bg-primary/30 text-primary animate-pulse"
                                  : "bg-severity-low/30 text-severity-low animate-pulse"
                                : entry.speaker === "patient"
                                  ? "hover:bg-primary/20 text-primary"
                                  : "hover:bg-severity-low/20 text-severity-low"
                            }`}
                          >
                            <Volume2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  <div ref={logEndRef} className="h-4" />
                </>
              )}
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
