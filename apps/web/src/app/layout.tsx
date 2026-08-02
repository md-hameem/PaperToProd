import type { Metadata } from "next";
import { ThemeProvider } from "@/providers/theme-provider";
import { WorkspaceProvider } from "@/contexts/WorkspaceContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "PaperToProd — Research Paper to Running Code",
  description:
    "AI-powered research reproduction engine. Paste an academic paper, get a validated, containerized repository with every design decision traceable back to the source text.",
  keywords: [
    "research reproduction",
    "academic papers",
    "AI code generation",
    "machine learning",
    "computer vision",
    "NLP",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <WorkspaceProvider>
            {children}
          </WorkspaceProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
