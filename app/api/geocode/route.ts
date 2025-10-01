export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const pincode = searchParams.get("pincode");
  if (!pincode) return new Response(JSON.stringify({ error: "pincode required" }), { status: 400 });
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(pincode)}`;
  const res = await fetch(url, { headers: { "User-Agent": "soothify-app/1.0" } });
  const data = await res.json();
  if (!Array.isArray(data) || data.length === 0) return new Response(JSON.stringify(null), { status: 200 });
  const { lat, lon } = data[0];
  return new Response(JSON.stringify({ lat: Number(lat), lon: Number(lon) }), { headers: { "content-type": "application/json" } });
}
