import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataNexus | Enterprise Intelligence",
  description: "Aviation data intelligence and operational reliability portal",
};
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
