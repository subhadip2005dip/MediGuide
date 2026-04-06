"use client";

import Link from "next/link";
import { NavBar } from "@/components/NavBar";
import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { Stats } from "@/components/Stats";
import { motion } from "framer-motion";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary selection:text-black">
      <NavBar />
      <main>
        <Hero />
        <Stats />
        <Features />
      </main>
      <footer className="py-24 border-t border-white/10 bg-black text-center relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-[radial-gradient(ellipse,_rgba(0,212,168,0.03)_0%,_transparent_70%)] pointer-events-none" />

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="container mx-auto px-4 relative z-10"
        >
          <h2 className="text-5xl md:text-8xl font-bebas text-white mb-8">
            FOR THE <span className="text-primary">BRAVE</span>.
          </h2>
          <div className="flex flex-wrap justify-center gap-12 text-sm uppercase tracking-widest text-white/50 mb-12">
            <Link
              href="#features"
              className="hover:text-primary transition-colors"
            >
              Features
            </Link>
            <Link
              href="#impact"
              className="hover:text-primary transition-colors"
            >
              Impact
            </Link>
            <Link
              href="/terms"
              className="hover:text-primary transition-colors"
            >
              Terms of Service
            </Link>
          </div>
          <p className="text-white/20 text-xs tracking-widest leading-loose">
            © {new Date().getFullYear()} MEDIROAM | AI-DRIVEN GLOBAL HEALTHCARE
            ACCESSIBILITY.
          </p>
        </motion.div>
      </footer>
    </div>
  );
}
