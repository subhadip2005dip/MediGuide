"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="relative flex min-h-[calc(100vh-64px)] flex-col items-center justify-center overflow-hidden px-4 py-16 text-center grid-bg">
      {/* Radial glow */}
      <div className="absolute top-[30%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[radial-gradient(ellipse,_rgba(0,212,168,0.07)_0%,_transparent_70%)] pointer-events-none" />

      {/* Scan line effect */}
      <div className="scan-line" />

      {/* Eyebrow */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="mb-8"
      >
        <Badge
          variant="outline"
          className="bg-primary/10 border-primary/20 text-primary px-4 py-1 flex items-center gap-2"
        >
          <span className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_var(--primary)] animate-pulse" />
          <span className="text-[0.8rem] font-semibold tracking-widest">
            AI-POWERED MEDICAL ASSISTANCE
          </span>
        </Badge>
      </motion.div>

      {/* Headline */}
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="mb-6 max-w-4xl text-5xl font-bebas leading-[0.9] tracking-tight text-white md:text-8xl"
      >
        YOUR DOCTOR.{" "}
        <span className="text-primary drop-shadow-[0_0_30px_rgba(0,212,168,0.4)]">
          ANYWHERE
        </span>{" "}
        IN THE WORLD.
      </motion.h1>

      {/* Subtext */}
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="mb-10 max-w-xl text-lg leading-relaxed text-white/70"
      >
        You&apos;re sick, alone, in a country where you don&apos;t speak the
        language. <strong className="text-white">MediGuide</strong> finds the
        right doctor, explains your symptoms, and keeps your family informed.
      </motion.p>

      {/* CTAs */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="flex flex-wrap justify-center gap-4"
      >
        <Link href="/triage">
          <Button
            size="lg"
            className="bg-primary text-black hover:bg-primary/90 text-lg px-10 py-7"
          >
            I Need Help Now <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </Link>
        <Link href="#features">
          <Button
            size="lg"
            variant="ghost"
            className="text-white hover:text-primary text-lg px-8 py-7 border border-white/10 hover:border-primary/50"
          >
            How It Works
          </Button>
        </Link>
      </motion.div>
    </section>
  );
}
