"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  SignInButton,
  SignOutButton,
  UserButton,
  useUser,
} from "@clerk/nextjs";

export function NavBar() {
  const user = useUser();

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
      className="sticky top-0 z-50 w-full border-b border-white/10 bg-black/60 backdrop-blur-md"
    >
      <div className="container mx-auto flex h-16 items-center justify-between px-4 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bebas text-2xl font-bold tracking-tight text-primary">
              MEDIGUIDE
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="#features"
              className="text-sm font-medium text-white/70 hover:text-primary transition-colors"
            >
              Features
            </Link>
            <Link
              href="#stats"
              className="text-sm font-medium text-white/70 hover:text-primary transition-colors"
            >
              Impact
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {user.isSignedIn ? (
            <UserButton />
          ) : (
            <Button
              variant="outline"
              className="text-white/70 hover:text-primary"
            >
              <SignInButton mode="modal" />
            </Button>
          )}
          <Link href="/triage">
            <Button className="bg-primary text-black hover:bg-primary/90">
              Get Help Now
            </Button>
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}
