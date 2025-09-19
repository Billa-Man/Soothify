"use client";
import { useMemo, useState } from 'react';

type Exercise = {
  title: string;
  url: string;
  category: 'Breathing' | 'Relaxation' | 'Mindfulness' | 'Meditation' | 'Visualization' | 'Movement';
  duration: number; // minutes
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  description: string;
  image?: string;
};

const EXERCISES: Exercise[] = [
  { title: '4-7-8 Powerful Breathing Technique', url: 'https://www.healthline.com/health/4-7-8-breathing', category: 'Breathing', duration: 5, difficulty: 'Beginner', description: 'A relaxation technique that calms the nervous system.' },
  { title: 'Progressive Muscle Relaxation', url: 'https://www.healthline.com/health/progressive-muscle-relaxation', category: 'Relaxation', duration: 15, difficulty: 'Intermediate', description: 'Release physical tension through systematic muscle relaxation.' },
  { title: 'Grounding Technique 5-4-3-2-1', url: 'https://www.urmc.rochester.edu/behavioral-health-partners/bhp-blog/april-2018/5-4-3-2-1-coping-technique-for-anxiety.aspx', category: 'Mindfulness', duration: 3, difficulty: 'Beginner', description: 'Engage your senses to manage anxiety and panic.' },
  { title: 'Body Scan Meditation', url: 'https://www.mindful.org/body-scan-meditation/', category: 'Meditation', duration: 10, difficulty: 'Intermediate', description: 'Focus attention on different parts of your body.' },
  { title: 'Safe Place Visualization', url: 'https://www.therapistaid.com/therapy-guide/visualization-guide', category: 'Visualization', duration: 7, difficulty: 'Beginner', description: 'Create a mental sanctuary to find peace and calmness.' },
  { title: 'Mindful Walking', url: 'https://www.mindful.org/how-to-do-walking-meditation/', category: 'Movement', duration: 10, difficulty: 'Beginner', description: 'Combine gentle walking with mindful awareness.' },
];

export default function Exercises() {
  const [dur, setDur] = useState<[number, number]>([0, 20]);
  const [diffs, setDiffs] = useState<Exercise['difficulty'][]>([]);
  const [cats, setCats] = useState<Exercise['category'][]>([]);

  const filtered = useMemo(() => EXERCISES.filter(e =>
    e.duration >= dur[0] && e.duration <= dur[1] &&
    (diffs.length ? diffs.includes(e.difficulty) : true) &&
    (cats.length ? cats.includes(e.category) : true)
  ), [dur, diffs, cats]);

  return (
    <main className="mx-auto max-w-6xl space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Mental Health Exercises</h1>
        <p className="muted">Quick, practical practices to help you reset.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <h3 className="font-medium mb-2">Filter Exercises</h3>
          <label className="block text-sm muted">Duration (minutes)</label>
          <div className="flex items-center gap-2">
            <input type="number" min={0} max={60} className="input w-24" value={dur[0]} onChange={(e)=>setDur([parseInt(e.target.value||'0',10), dur[1]])} />
            <span className="muted">-</span>
            <input type="number" min={0} max={60} className="input w-24" value={dur[1]} onChange={(e)=>setDur([dur[0], parseInt(e.target.value||'20',10)])} />
          </div>
          <div className="mt-3">
            <label className="block text-sm muted">Difficulty</label>
            {(['Beginner','Intermediate','Advanced'] as const).map(d => (
              <label key={d} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={diffs.includes(d)} onChange={(e)=> setDiffs(e.target.checked ? [...diffs, d] : diffs.filter(x=>x!==d))} /> {d}
              </label>
            ))}
          </div>
          <div className="mt-3">
            <label className="block text-sm muted">Category</label>
            {(['Breathing','Relaxation','Mindfulness','Meditation','Visualization','Movement'] as const).map(c => (
              <label key={c} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={cats.includes(c)} onChange={(e)=> setCats(e.target.checked ? [...cats, c] : cats.filter(x=>x!==c))} /> {c}
              </label>
            ))}
          </div>
        </div>
        <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((e) => (
            <a key={e.title} className="card p-4 hover:shadow-sm" href={e.url} target="_blank" rel="noreferrer">
              <div className="text-lg font-medium">{e.title}</div>
              <div className="text-sm muted">{e.description}</div>
              <div className="mt-2 text-sm" style={{ color: '#4f46e5' }}>{e.category} • ⏱️ {e.duration} • 📊 {e.difficulty}</div>
            </a>
          ))}
        </div>
      </div>
    </main>
  );
}
