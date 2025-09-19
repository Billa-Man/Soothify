"use client";
import { useMemo, useState } from 'react';

type Blog = { title: string; url: string; category: string; readTime: number; date: string; excerpt: string; image?: string };

const BLOGS: Blog[] = [
  { title: 'Understanding and Managing Panic Attacks', url: 'https://www.healthline.com/health/panic-attack', category: 'Mental Health', readTime: 5, date: '2024-02-15', excerpt: 'Learn about the science behind panic attacks and coping strategies.' },
  { title: 'Mindfulness Techniques for Anxiety Relief', url: 'https://www.mindful.org/how-to-manage-anxiety-with-mindfulness/', category: 'Wellness', readTime: 4, date: '2024-02-14', excerpt: 'Practical mindfulness exercises to reduce anxiety and promote well-being.' },
  { title: 'Exercise as a Natural Stress Reliever', url: 'https://www.mayoclinic.org/healthy-lifestyle/stress-management/in-depth/exercise-and-stress/art-20044469', category: 'Fitness', readTime: 5, date: '2024-02-11', excerpt: 'How physical activity can improve mental health and reduce stress.' },
  { title: 'Sleep and Mental Health: The Vital Connection', url: 'https://www.sleepfoundation.org/mental-health', category: 'Health', readTime: 7, date: '2024-02-12', excerpt: 'Explore the relationship between sleep quality and mental well-being.' },
  { title: 'Building a Strong Support System', url: 'https://www.psychologytoday.com/us/basics/social-support', category: 'Relationships', readTime: 6, date: '2024-02-13', excerpt: 'The importance of social connections for better mental health.' },
  { title: 'Digital Detox for Mental Clarity', url: 'https://www.verywellmind.com/why-and-how-to-do-a-digital-detox-4771321', category: 'Lifestyle', readTime: 4, date: '2024-02-10', excerpt: 'Benefits of taking breaks from technology and healthy digital routines.' },
];

export default function Blogs() {
  const [query, setQuery] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [maxTime, setMaxTime] = useState(10);

  const cats = useMemo(() => Array.from(new Set(BLOGS.map(b => b.category))), []);
  const filtered = useMemo(() => BLOGS.filter(b =>
    (!query || (b.title.toLowerCase().includes(query.toLowerCase()) || b.excerpt.toLowerCase().includes(query.toLowerCase()))) &&
    (categories.length ? categories.includes(b.category) : true) &&
    b.readTime <= maxTime
  ), [query, categories, maxTime]);

  return (
    <main className="mx-auto max-w-6xl space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Mental Health Resources</h1>
        <p className="muted">Curated reads to learn, reflect, and grow.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <h3 className="font-medium mb-2">Filters</h3>
          <label className="block text-sm muted">Search</label>
          <input className="input" placeholder="Search blogs" value={query} onChange={(e)=>setQuery(e.target.value)} />
          <div className="mt-3">
            <label className="block text-sm muted">Categories</label>
            {cats.map(c => (
              <label key={c} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={categories.includes(c)} onChange={(e)=> setCategories(e.target.checked ? [...categories, c] : categories.filter(x=>x!==c))} /> {c}
              </label>
            ))}
          </div>
          <div className="mt-3">
            <label className="block text-sm muted">Max reading time (minutes)</label>
            <input type="number" min={1} max={20} className="input" value={maxTime} onChange={(e)=>setMaxTime(parseInt(e.target.value||'10',10))} />
          </div>
        </div>
        <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((b) => (
            <a key={b.title} className="card p-4 hover:shadow-sm" href={b.url} target="_blank" rel="noreferrer">
              <div className="text-lg font-medium">{b.title}</div>
              <div className="text-sm muted">{b.excerpt}</div>
              <div className="mt-2 text-sm" style={{ color: '#4f46e5' }}>{b.category} • {b.readTime} min • {new Date(b.date).toLocaleDateString()}</div>
            </a>
          ))}
        </div>
      </div>
    </main>
  );
}
