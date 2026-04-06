"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Activity, Hospital, Share2 } from "lucide-react";

const FEATURES = [
  {
    icon: Activity,
    title: "AI Triage",
    desc: "Describe your symptoms in any language. Our clinical AI assesses severity in seconds.",
  },
  {
    icon: Hospital,
    title: "Live Hospital Matching",
    desc: "Real hospitals near you, ranked by specialty match, distance, and availability.",
  },
  {
    icon: Share2,
    title: "Family Updates",
    desc: "One tap sends a clear, compassionate medical summary to your loved ones.",
  },
];

export function Features() {
  return (
    <section
      id="features"
      className="py-24 px-4 bg-background relative overflow-hidden"
    >
      <div className="container mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <Badge
            variant="outline"
            className="mb-4 text-primary bg-primary/10 border-primary/20"
          >
            FEATURES
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bebas text-white">
            CLINICAL TOOLS FOR THE MODERN TRAVELER.
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {FEATURES.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
            >
              <Card className="h-full bg-white/5 border-white/10 hover:border-primary/50 hover:bg-white/10 transition-all group overflow-hidden relative">
                <div className="absolute top-0 right-0 p-4 opacity-10 -mr-6 -mt-6 group-hover:opacity-20 transition-opacity">
                  <feature.icon size={120} />
                </div>
                <CardHeader>
                  <feature.icon className="w-12 h-12 text-primary mb-4" />
                  <CardTitle className="text-2xl font-bebas text-white group-hover:text-primary transition-colors">
                    {feature.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-white/60 leading-relaxed">
                  {feature.desc}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
