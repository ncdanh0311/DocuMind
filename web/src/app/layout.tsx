import type { Metadata } from "next";
import { Outfit, Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin", "latin-ext"],
  weight: ["500", "600", "700", "800"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "DocuMind - Trợ lý Sổ tay Cá nhân AI",
  description: "Trợ lý sổ tay cá nhân AI hỗ trợ quản lý và tóm tắt tài liệu học tập, nghiên cứu thông minh",
  icons: {
    icon: "/assets/mascot/mascot-owl-avatar-circle.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className={`${outfit.variable} ${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#F7FAF7] text-[#2D3E50] antialiased selection:bg-[#E0F2F1] selection:text-[#26A69A]">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
