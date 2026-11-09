import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const outfit = localFont({ src: './fonts/outfit.ttf', variable: '--font-outfit', weight: '100 900', display: 'swap' });
const inter = localFont({ src: './fonts/inter.ttf', variable: '--font-inter', weight: '100 900', display: 'swap' });

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
