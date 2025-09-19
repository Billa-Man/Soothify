'use client';
import { useEffect, useMemo, useState } from 'react';
import type { Data } from 'plotly.js';
import dynamic from 'next/dynamic';
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function Dashboard() {
  const [users, setUsers] = useState<string[]>([]);
  const [userId, setUserId] = useState('');
  const [data, setData] = useState<any[]>([]);
  const [start, setStart] = useState<string>('');
  const [end, setEnd] = useState<string>('');

  // load users
  useEffect(() => {
    (async () => {
      const res = await fetch('/api/users');
      const list: string[] = await res.json();
      setUsers(list);
      if (!userId && list.length) setUserId(list[0]);
    })();
  }, []);

  useEffect(() => {
    (async () => {
      if (!userId) return;
      const qs = new URLSearchParams();
      if (start) qs.set('start', start);
      if (end) qs.set('end', end);
      const url = `/api/user-data/${userId}` + (qs.toString() ? `?${qs}` : '');
      const res = await fetch(url);
      const docs = await res.json();
      setData(docs);
    })();
  }, [userId, start, end]);

  const moodHistory = useMemo(() => data.flatMap((d) => d.mood_history || []), [data]);
  const panicEpisodes = useMemo(() => data.flatMap((d) => d.panic_episodes || []).map((x: string) => new Date(x)), [data]);
  const byDate = useMemo(() => {
    const map = new Map<string, { moods: string[] }>();
    for (const m of moodHistory) {
      const d = new Date(m.timestamp);
      const key = new Date(d.getFullYear(), d.getMonth(), d.getDate()).toISOString();
      const entry = map.get(key) || { moods: [] };
      entry.moods.push(m.mood);
      map.set(key, entry);
    }
    return map;
  }, [moodHistory]);
  const longestStreak = useMemo(() => {
    if (byDate.size === 0) return 0;
    const days = Array.from(byDate.keys()).map((k) => new Date(k)).sort((a,b)=>a.getTime()-b.getTime());
    let best = 1, cur = 1;
    for (let i=1;i<days.length;i++) {
      const diff = (days[i].getTime() - days[i-1].getTime()) / (24*60*60*1000);
      if (diff === 1) { cur += 1; best = Math.max(best, cur); } else { cur = 1; }
    }
    return best;
  }, [byDate]);
  const consistencyPct = useMemo(() => {
    if (byDate.size === 0) return 0;
    const sorted = Array.from(byDate.keys()).map((k)=>new Date(k)).sort((a,b)=>a.getTime()-b.getTime());
    const first = sorted[0];
    const totalDays = Math.floor((new Date().getTime() - first.getTime())/(24*60*60*1000)) + 1;
    return Math.round((byDate.size / totalDays) * 1000) / 10; // one decimal
  }, [byDate]);
  const panicHours = useMemo(() => panicEpisodes.map((d)=>d.getHours()), [panicEpisodes]);
  const activityImpact = useMemo(() => {
    if (!data.length) return null as null | Record<string, {positive:number, neutral:number, negative:number}>;
    const last = data[data.length - 1];
    return last.activity_impact || null;
  }, [data]);
  const calendar = useMemo(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const firstDay = new Date(year, month, 1);
    const startWeekday = firstDay.getDay(); // 0 Sun - 6 Sat
    const daysInMonth = new Date(year, month+1, 0).getDate();
    const rows: Array<Array<string>> = [];
    const MOJI: Record<string,string> = { Happy:'😊', Neutral:'😐', Anxious:'😰', Sad:'😢', Depressed:'😔' };
    let day = 1;
    for (let r=0; r<6; r++) {
      const row: string[] = [];
      for (let c=0; c<7; c++) {
        const cellIndex = r*7 + c;
        if (cellIndex < startWeekday || day > daysInMonth) { row.push(''); continue; }
        const key = new Date(year, month, day).toISOString();
        const entry = byDate.get(key);
        if (entry && entry.moods.length) {
          // choose dominant mood (mode)
          const freq: Record<string, number> = {};
          for (const m of entry.moods) freq[m] = (freq[m]||0)+1;
          const dom = Object.entries(freq).sort((a,b)=>b[1]-a[1])[0][0];
          row.push(`${day} ${MOJI[dom]||''}`);
        } else {
          row.push(String(day));
        }
        day++;
      }
      rows.push(row);
      if (day > daysInMonth) break;
    }
    return rows;
  }, [byDate]);
  const logMood = async (mood: string) => {
    if (!userId) return;
    const today = new Date();
    await fetch(`/api/user-data/${userId}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ date: today.toISOString(), mood_entry: { timestamp: today.toISOString(), mood } }),
    });
    // refresh
    const res = await fetch(`/api/user-data/${userId}`);
    const docs = await res.json();
    setData(docs);
  };

  return (
    <main className="mx-auto max-w-5xl space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Mental Health Dashboard</h1>
        <p className="muted">Explore your patterns and keep a gentle routine.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
        <div>
          <label className="block text-sm muted">User</label>
          <select className="input" value={userId} onChange={(e)=>setUserId(e.target.value)}>
            {users.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm muted">Start</label>
          <input type="date" className="input" value={start} onChange={(e)=>setStart(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm muted">End</label>
          <input type="date" className="input" value={end} onChange={(e)=>setEnd(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm muted">Log Mood</label>
          <div className="flex gap-2">
            {['Happy','Neutral','Anxious','Sad','Depressed'].map(m => (
              <button key={m} className="btn btn-outline" onClick={()=>logMood(m)}>{m}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <h3 className="font-medium">Panic Episodes (7d)</h3>
          <p className="text-3xl">{panicEpisodes.filter((d: Date) => Date.now() - d.getTime() < 7*24*60*60*1000).length}</p>
        </div>
        <div className="card p-4">
          <h3 className="font-medium">Mood Entries</h3>
          <p className="text-3xl">{moodHistory.length}</p>
        </div>
        <div className="card p-4">
          <h3 className="font-medium">Longest Streak</h3>
          <p className="text-3xl">{longestStreak} days</p>
        </div>
      </div>

      <div className="card p-4">
        <h3 className="font-medium mb-2">Mood Trends</h3>
        <Plot
          data={[{ x: moodHistory.map((m:any)=>new Date(m.timestamp)), y: moodHistory.map((m:any)=>m.mood), type: 'scatter', mode: 'lines+markers' }]}
          layout={{ autosize: true, height: 360 }}
          style={{ width: '100%' }}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-4">
          <h3 className="font-medium mb-2">Panic Episode Patterns (by hour)</h3>
          <Plot
            data={[{ x: panicHours, type: 'histogram', xbins: { start: 0, end: 24, size: 1 } }]}
            layout={{ autosize: true, height: 320, xaxis: { title: { text: 'Hour of Day' }, dtick: 1 } }}
            style={{ width: '100%' }}
          />
        </div>
        <div className="card p-4">
          <h3 className="font-medium mb-2">Activity Impact Analysis</h3>
          {activityImpact ? (() => {
            const cats = ['Exercise','Meditation','Social Activities'] as const;
            const xPos = cats.map((c) => activityImpact[c]?.positive ?? 0);
            const xNeu = cats.map((c) => activityImpact[c]?.neutral ?? 0);
            const xNeg = cats.map((c) => activityImpact[c]?.negative ?? 0);
            const traces: Data[] = [
              { y: cats as unknown as string[], x: xPos, type: 'bar', orientation: 'h', name: 'Positive', marker: { color: '#7792E3' } },
              { y: cats as unknown as string[], x: xNeu, type: 'bar', orientation: 'h', name: 'Neutral', marker: { color: '#E3E3E3' } },
              { y: cats as unknown as string[], x: xNeg, type: 'bar', orientation: 'h', name: 'Negative', marker: { color: '#FFB4B4' } },
            ];
            return (
              <Plot
                data={traces}
                layout={{ autosize: true, height: 320, barmode: 'stack' }}
                style={{ width: '100%' }}
              />
            );
          })() : (
            <p className="muted">No activity impact data.</p>
          )}
        </div>
      </div>

      <div className="card p-4">
        <h3 className="font-medium mb-2">Monthly Overview</h3>
        <div className="overflow-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left">
                {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => <th key={d} className="px-2 py-1 muted">{d}</th>)}
              </tr>
            </thead>
            <tbody>
              {calendar.map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => (
                    <td key={j} className="border px-2 py-1 align-top w-24 h-12">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 muted">Check-in consistency: <b>{consistencyPct}%</b></p>
      </div>
    </main>
  );
}
