import type { Metadata } from "next";
import { HeroUIProvider } from "@heroui/react";
import SiteFooter from "@/app/components/SiteFooter";
import "./globals.css";

export const metadata: Metadata = {
  title: "PvPogo",
  description:
    "Unofficial fan-made PvP battle analysis and team building. Not affiliated with Nintendo, The Pokémon Company, or Niantic.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="light">
      <body>
        <HeroUIProvider>
          <div className="flex min-h-screen flex-col">
            <div className="flex-1">{children}</div>
            <SiteFooter />
          </div>
        </HeroUIProvider>
      </body>
    </html>
  );
}
