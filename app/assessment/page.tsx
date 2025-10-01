'use client';
import { useCallback, useEffect, useMemo, useState } from 'react';

const questions = [
  { text: 'Over the past 2 weeks, how often have you felt down, depressed, or hopeless?', options: ['Not at all', 'Several days', 'More than half the days', 'Nearly every day'], weights: [0,1,2,3] },
  { text: 'How often do you feel overwhelmed by your daily responsibilities?', options: ['Never', 'Sometimes', 'Often', 'Always'], weights: [0,1,2,3] },
  { text: 'How would you rate your sleep quality over the past week?', options: ['Excellent', 'Good', 'Fair', 'Poor'], weights: [0,1,2,3] },
  { text: 'How often do you feel anxious or worried about various aspects of your life?', options: ['Rarely', 'Occasionally', 'Frequently', 'Constantly'], weights: [0,1,2,3] },
  { text: 'How would you describe your energy levels throughout the day?', options: ['Very energetic', 'Moderately energetic', 'Low energy', 'Extremely fatigued'], weights: [0,1,2,3] },
  { text: 'How often do you have trouble concentrating on tasks?', options: ['Rarely', 'Sometimes', 'Often', 'Almost always'], weights: [0,1,2,3] },
  { text: 'How would you rate your stress levels in the past month?', options: ['Low', 'Moderate', 'High', 'Very high'], weights: [0,1,2,3] },
  { text: 'How often do you feel isolated or lonely?', options: ['Never', 'Occasionally', 'Frequently', 'Almost always'], weights: [0,1,2,3] },
  { text: 'How would you rate your ability to cope with challenges?', options: ['Very good', 'Good', 'Fair', 'Poor'], weights: [0,1,2,3] },
  { text: 'How often do you experience physical symptoms of stress (headaches, tension, etc.)?', options: ['Rarely', 'Sometimes', 'Often', 'Very often'], weights: [0,1,2,3] },
];

export default function Assessment() {
  const [users, setUsers] = useState<string[]>([]);
  const [userId, setUserId] = useState('');
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<number[]>(Array(questions.length).fill(0));
  const [last, setLast] = useState<{ date: string; severity: string; percentage: number } | null>(null);

  const fetchUsers = useCallback(async () => {
    const res = await fetch('/api/users');
    const list: string[] = await res.json();
    setUsers(list);
    if (!userId && list.length) setUserId(list[0]);
  }, [userId]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    (async () => {
      if (!userId) return;
      const res = await fetch(`/api/assessments?user_id=${encodeURIComponent(userId)}`);
      const json = await res.json();
      if (json) setLast({ date: json.date, severity: json.severity, percentage: json.percentage });
    })();
  }, [userId]);

  const score = useMemo(() => answers.reduce((s, v, i) => s + questions[i].weights[v], 0), [answers]);
  const maxScore = useMemo(() => questions.reduce((s, q) => s + Math.max(...q.weights), 0), []);
  const pct = Math.round((score / maxScore) * 100);

  const severity = pct < 30 ? 'mild' : pct < 60 ? 'moderate' : 'severe';

  const onSelect = (optionIndex: number) => {
    const next = [...answers];
    next[idx] = optionIndex;
    setAnswers(next);
  };

  const submit = async () => {
    await fetch('/api/assessments', { method: 'POST', body: JSON.stringify({ user_id: userId || 'demo', date: new Date(), severity, score, percentage: pct }) });
    setLast({ date: new Date().toISOString(), severity, percentage: pct });
  };

  return (
    <main className="mx-auto max-w-2xl space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Mental Health Assessment</h1>
        <p className="muted">Answer a few questions to get a quick snapshot.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
        <div>
          <label className="block text-sm muted">User</label>
          <select className="input" value={userId} onChange={(e)=>setUserId(e.target.value)}>
            {users.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>
        {last && (
          <div className="text-sm muted">Last: {new Date(last.date).toLocaleString()} • Severity: <b>{last.severity}</b> • {last.percentage}%</div>
        )}
      </div>

      {idx < questions.length ? (
        <div className="space-y-4">
          <div className="w-full h-2 rounded bg-[#eef2ff]">
            <div className="h-2 rounded bg-indigo-500" style={{ width: `${(idx / questions.length) * 100}%` }} />
          </div>
          <p className="text-sm muted">Question {idx + 1} of {questions.length}</p>
          <div className="card p-4">
            <p>{questions[idx].text}</p>
          </div>
          <div className="space-y-2">
            {questions[idx].options.map((opt, i) => (
              <label key={i} className="flex items-center gap-2">
                <input type="radio" name="opt" checked={answers[idx]===i} onChange={() => onSelect(i)} />
                <span>{opt}</span>
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button className="btn btn-outline" disabled={idx===0} onClick={() => setIdx(idx-1)}>Previous</button>
            <button className="btn btn-primary" onClick={() => setIdx(idx+1)}>{idx < questions.length - 1 ? 'Next' : 'Submit'}</button>
          </div>
        </div>
      ) : (
        <div className="card p-6 text-center space-y-3">
          <h2 className="text-xl font-medium">Assessment Complete</h2>
          <p className="muted">Severity: <b>{severity}</b> • Score: {score} • {pct}%</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {severity === 'mild' && (
              <>
                <a className="btn btn-outline" href="/chat">AI Chat</a>
                <a className="btn btn-outline" href="/blogs">Wellness Blogs</a>
                <a className="btn btn-outline" href="/exercises">Guided Exercises</a>
              </>
            )}
            {severity === 'moderate' && (
              <a className="btn btn-outline" href="/chat">AI Chat</a>
            )}
            {severity === 'severe' && (
              <a className="btn btn-outline" href="/facilities">Find Facilities</a>
            )}
          </div>
          <button onClick={submit} className="btn btn-primary">Save Result</button>
        </div>
      )}
    </main>
  );
}
