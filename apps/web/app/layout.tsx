import type { Metadata } from "next";
import { DataModeProvider } from "@/components/ui/DataModeProvider";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "FireFusion",
    template: "%s | FireFusion",
  },
  description: "A transparent view of harmonized MODIS and VIIRS fire detections.",
  icons: {
    icon: "/images/app-icon.jpeg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetBrainsMono.variable}`}
    >
      <body>
        <DataModeProvider>{children}</DataModeProvider>
      </body>
    </html>
  );
}
