import Link from "next/link";
import Image from "next/image";

const cards = [
  { title: "Begin Assessment", href: "/assessment", desc: "10 quick questions to personalize your journey." },
  { title: "AI Chat", href: "/chat", desc: "Talk to an assistant that listens and guides." },
  { title: "Dashboard", href: "/dashboard", desc: "Track moods, patterns, and progress." },
  { title: "Hume Voice", href: "/hume", desc: "Try empathic voice with the Hume EVI SDK." },
  { title: "Facilities", href: "/facilities", desc: "Find nearby mental health facilities." },
  { title: "Exercises", href: "/exercises", desc: "Short practices to calm and reset." },
  { title: "Blogs", href: "/blogs", desc: "Curated learning to support your wellness." },
];

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="text-center pt-6">
        <div className="inline-flex items-center gap-3">
          <Image src="/media/mainlogo.png" alt="Soothify" width={60} height={60} className="rounded" />
          <div className="text-left">
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Your Mental Health Companion</h1>
            <p className="text-slate-600">Simple tools, gentle guidance, and clear insights.</p>
          </div>
        </div>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Link href="/assessment" className="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700">Start Assessment</Link>
          <Link href="/chat" className="px-4 py-2 rounded border hover:bg-slate-50">Open AI Chat</Link>
        </div>
      </section>

      <section>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map((c) => (
            <Link key={c.href} href={c.href} className="group rounded-xl border p-4 hover:shadow-sm transition-shadow bg-white">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium group-hover:text-indigo-600">{c.title}</h3>
                <span className="text-slate-400">→</span>
              </div>
              <p className="text-slate-600 text-sm mt-1">{c.desc}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
