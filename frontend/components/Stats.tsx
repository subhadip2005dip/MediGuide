"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";

const STATS = [
  { value: "2.3B", label: "travelers yearly" },
  { value: "68%", label: "face language barriers" },
  { value: "4.2min", label: "avg response time" },
];

export function Stats() {
  return (
    <section
      id="stats"
      className="py-32 px-4 bg-black relative border-y border-white/10"
    >
      <div className="container mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="flex flex-wrap justify-center gap-16 md:gap-32"
        >
          {STATS.map((s, index) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="text-center group"
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                className="font-bebas text-6xl md:text-8xl text-primary drop-shadow-[0_0_20px_rgba(0,212,168,0.2)] group-hover:drop-shadow-[0_0_40px_rgba(0,212,168,0.5)] transition-all"
              >
                {s.value}
              </motion.div>
              <div className="text-white/40 font-medium tracking-widest text-sm uppercase mt-4">
                {s.label}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
