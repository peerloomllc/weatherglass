#!/usr/bin/env python3
"""Build app/src/main/assets/basemap.bin, the map screen's built-in outlines.

Source: Natural Earth (public domain), from
https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
  ne_50m_coastline, ne_50m_admin_0_boundary_lines_land,
  ne_50m_admin_1_states_provinces_lines, ne_50m_lakes,
  ne_10m_populated_places_simple

  python3 tools/basemap.py <folder with those .geojson files>

Format (little endian), read by ui/MapData.kt:
  "WGM1"
  4 layers (coast, borders, states, lakes), each:
    u32 line count, then per line: u16 point count, then float32 lon, lat pairs
  cities: u32 count, then per city: float32 lon, lat, u32 population,
    u8 name length, UTF-8 name
"""
import json
import os
import struct
import sys

TOL = 0.01  # degrees: drop detail smaller than about 1 km
MIN_POP = 50_000


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x0, y0), (x1, y1) = pts[a], pts[b]
        dx, dy = x1 - x0, y1 - y0
        d2 = dx * dx + dy * dy
        best, idx = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            if d2 == 0:
                dist = (px - x0) ** 2 + (py - y0) ** 2
            else:
                t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / d2))
                dist = (px - x0 - t * dx) ** 2 + (py - y0 - t * dy) ** 2
            if dist > best:
                best, idx = dist, i
        if idx >= 0 and best > tol * tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


def lines(path):
    out = []
    for f in json.load(open(path))["features"]:
        g = f["geometry"]
        if g is None:
            continue
        t, c = g["type"], g["coordinates"]
        parts = {"LineString": [c], "MultiLineString": c, "Polygon": c,
                 "MultiPolygon": [r for poly in c for r in poly]}.get(t, [])
        for p in parts:
            s = simplify([(float(x), float(y)) for x, y, *_ in p], TOL)
            if len(s) >= 2:
                # Split very long lines so the point count fits in a u16.
                for i in range(0, len(s) - 1, 60000):
                    out.append(s[i:i + 60001])
    return out


def main():
    src = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "app", "src", "main", "assets", "basemap.bin")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    b = bytearray(b"WGM1")
    total = 0
    for name in ("ne_50m_coastline", "ne_50m_admin_0_boundary_lines_land",
                 "ne_50m_admin_1_states_provinces_lines", "ne_50m_lakes"):
        ls = lines(os.path.join(src, name + ".geojson"))
        b += struct.pack("<I", len(ls))
        for l in ls:
            b += struct.pack("<H", len(l))
            for x, y in l:
                b += struct.pack("<ff", x, y)
            total += len(l)
        print(name, len(ls), "lines")
    cities = []
    for f in json.load(open(os.path.join(src, "ne_10m_populated_places_simple.geojson")))["features"]:
        p = f["properties"]
        pop = int(p.get("pop_max") or 0)
        if pop >= MIN_POP:
            x, y = f["geometry"]["coordinates"][:2]
            cities.append((float(x), float(y), pop, (p.get("name") or "").encode()[:255]))
    cities.sort(key=lambda c: -c[2])
    b += struct.pack("<I", len(cities))
    for x, y, pop, n in cities:
        b += struct.pack("<ffIB", x, y, pop, len(n)) + n
    open(dst, "wb").write(b)
    print(f"{total} points, {len(cities)} cities, {len(b) / 1e6:.2f} MB -> {dst}")


if __name__ == "__main__":
    main()
