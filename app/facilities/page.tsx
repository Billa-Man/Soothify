'use client';
import { useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import type { FC } from 'react';

const MapContainer = dynamic(
  () => import('react-leaflet').then(m => m.MapContainer),
  { ssr: false }
) as FC<{ center: [number, number]; zoom: number; children: React.ReactNode; style?: React.CSSProperties }>;

const TileLayer = dynamic(
  () => import('react-leaflet').then(m => m.TileLayer),
  { ssr: false }
) as FC<{ url: string; attribution: string }>;

const Marker = dynamic(
  () => import('react-leaflet').then(m => m.Marker),
  { ssr: false }
) as FC<{ position: [number, number]; children?: React.ReactNode }>;

const Circle = dynamic(
  () => import('react-leaflet').then(m => m.Circle),
  { ssr: false }
) as FC<{ center: [number, number]; radius: number; pathOptions?: { color: string } }>;

type Coords = { lat: number; lon: number };
type Facility = { name: string; address: string; phone: string; services: string[]; emergency: boolean; coords?: [number, number] };

const FACILITIES: Facility[] = [
  { name: 'Mental Health Center A', address: '123 Health St', phone: '(555) 123-4567', services: ['Counseling','Psychiatry','Group Therapy'], emergency: true },
  { name: 'Wellness Clinic B', address: '456 Care Ave', phone: '(555) 987-6543', services: ['Individual Therapy','Crisis Intervention'], emergency: false },
];

export default function Facilities() {
  const [pincode, setPincode] = useState('');
  const [radiusKm, setRadiusKm] = useState(10);
  const [coords, setCoords] = useState<Coords | null>(null);

  const find = async () => {
    const res = await fetch(`/api/geocode?pincode=${encodeURIComponent(pincode)}`);
    const json = await res.json();
    setCoords(json);
  };

  const facilities = useMemo(() => {
    if (!coords) return [] as Facility[];
    // mock coordinates slightly offset from user location
    return FACILITIES.map((f, i) => ({ ...f, coords: [coords.lat + 0.01 * (i+1), coords.lon + 0.01 * (i+1)] as [number, number] }));
  }, [coords]);

  return (
    <main className="mx-auto max-w-5xl space-y-4">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Find Mental Health Facilities Near You</h1>
        <p className="muted">Search by pincode and choose a comfortable radius.</p>
      </div>

      <div className="card p-4 grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
        <div className="md:col-span-2">
          <label className="block text-sm muted">Pincode</label>
          <input className="input" placeholder="Enter your pincode" value={pincode} onChange={(e)=>setPincode(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm muted">Search radius (km)</label>
          <input type="number" min={1} max={50} className="input" value={radiusKm} onChange={(e)=>setRadiusKm(parseInt(e.target.value||'10', 10))} />
        </div>
        <div>
          <button className="btn btn-primary w-full" onClick={find}>Find Facilities</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 card overflow-hidden">
          {coords ? (
            <div className="h-[420px]">
              <MapContainer center={[coords.lat, coords.lon] as [number, number]} zoom={12} style={{ height: '100%', width: '100%' }}>
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors" />
                <Marker position={[coords.lat, coords.lon] as [number, number]} />
                <Circle center={[coords.lat, coords.lon] as [number, number]} radius={radiusKm * 1000} pathOptions={{ color: '#7792E3' }} />
                {facilities.map((f) => f.coords && <Marker key={f.name} position={f.coords} />)}
              </MapContainer>
            </div>
          ) : (
            <div className="p-6 muted">Enter a pincode to view nearby facilities.</div>
          )}
        </div>
        <div className="space-y-3">
          <div className="card p-4 border-red-100" style={{ borderColor: '#fecaca' }}>
            <h3 className="font-medium" style={{ color: '#dc2626' }}>In case of emergency</h3>
            <ul className="text-sm" style={{ color: '#b91c1c' }}>
              <li>Call emergency services (911)</li>
              <li>National Crisis Hotline: 988</li>
              <li>Nearest emergency room</li>
            </ul>
          </div>
          {facilities.map((f) => (
            <div key={f.name} className="card p-4">
              <h4 className="font-medium">{f.name}</h4>
              <p className="text-sm">📍 {f.address}</p>
              <p className="text-sm">📞 {f.phone}</p>
              <p className="text-sm">🏥 Services: {f.services.join(', ')}</p>
              {f.emergency && <p className="text-sm" style={{ color: '#dc2626' }}>🚨 24/7 Emergency Services Available</p>}
              <a className="inline-block mt-2 btn btn-primary" href={`tel:${f.phone}`}>Contact Facility</a>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
