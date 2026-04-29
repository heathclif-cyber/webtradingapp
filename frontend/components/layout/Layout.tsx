import { ReactNode } from "react";
import Navbar from "./Navbar";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      <Navbar />
      <main className="max-w-screen-2xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
