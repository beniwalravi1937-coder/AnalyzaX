import type { Row } from "./types";

function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const REGIONS = ["North", "South", "East", "West", "Central"];
const CHANNELS = ["Organic", "Paid Search", "Referral", "Email", "Partner"];
const SEGMENTS = ["SMB", "Mid-Market", "Enterprise"];
const PRODUCTS = ["Starter", "Growth", "Scale", "Enterprise"];

export const SAMPLE_COLUMNS = [
  "order_id",
  "order_date",
  "region",
  "channel",
  "segment",
  "product",
  "units",
  "unit_price",
  "revenue",
  "discount_pct",
  "satisfaction",
];

export function buildSampleRows(): Row[] {
  const rnd = mulberry32(20260911);
  const rows: Row[] = [];
  const start = new Date("2025-01-06").getTime();
  for (let i = 0; i < 720; i++) {
    const day = new Date(start + Math.floor(rnd() * 300) * 86400000);
    const segment = SEGMENTS[Math.floor(rnd() * SEGMENTS.length)];
    const product = PRODUCTS[Math.floor(rnd() * PRODUCTS.length)];
    const units = 1 + Math.floor(rnd() * (segment === "Enterprise" ? 60 : 14));
    const price = Math.round((80 + rnd() * 420) * 100) / 100;
    const discount = Math.round(rnd() * 25 * 10) / 10;
    const revenue = Math.round(units * price * (1 - discount / 100) * 100) / 100;
    const missingSat = rnd() < 0.12;
    rows.push({
      order_id: `ORD-${(10000 + i).toString()}`,
      order_date: day.toISOString().slice(0, 10),
      region: REGIONS[Math.floor(rnd() * REGIONS.length)],
      channel: rnd() < 0.05 ? null : CHANNELS[Math.floor(rnd() * CHANNELS.length)],
      segment,
      product,
      units,
      unit_price: price,
      revenue: rnd() < 0.02 ? Math.round(revenue * 14) : revenue,
      discount_pct: discount,
      satisfaction: missingSat ? null : Math.round((3 + rnd() * 2) * 10) / 10,
    });
  }
  // a few exact duplicates so the cleaning page has something real to fix
  rows.push({ ...rows[4] }, { ...rows[91] }, { ...rows[250] });
  return rows;
}
