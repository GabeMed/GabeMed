#!/usr/bin/env python3
"""Render the profile's telemetry panel from the GitHub GraphQL API.

Writes four SVGs to assets/telemetry/: dark and light, wide and narrow.

Token: STATS_TOKEN if set, else GITHUB_TOKEN. The contribution calendar,
the private share and the per-year totals are public (the profile shares
private contribution counts anonymously), so any token reads them. The
merged-PR total is drawn only when STATS_TOKEN is set and can see at least
one merged PR in a private repo; with GITHUB_TOKEN that number would come
out misleadingly low, so the panel leaves it out.

Only aggregate counts are requested: no repository or organization names.
Standard library only.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com/graphql"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"
ADV = 0.602  # advance width of the monospace stack, in em

THEMES = {
    "dark": dict(
        bg="#010409", border="#30363d", bar="#0d1117", text="#e6edf3", muted="#8b949e", dim="#3d444d",
        accent="#56d4bb", major="#1a2029", axis="#2a313b", raw="#6e7681", fill=".30",
    ),
    "light": dict(
        bg="#f6f8fa", border="#d0d7de", bar="#eef1f4", text="#1f2328", muted="#59636e", dim="#afb8c1",
        accent="#087f6d", major="#dbe1e7", axis="#c5cdd5", raw="#8c959f", fill=".20",
    ),
}

WEEKS = 52
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


# ---------------------------------------------------------------- data

def graphql(token, query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "profile-telemetry",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                out = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == 2:
                raise SystemExit(f"GitHub API: HTTP {e.code}")
        except urllib.error.URLError as e:
            if attempt == 2:
                raise SystemExit(f"GitHub API: {e.reason}")
        time.sleep(5 * (attempt + 1))
    if out.get("errors"):
        raise SystemExit("GitHub API: " + "; ".join(e.get("message", "?") for e in out["errors"]))
    return out["data"]


BY_REPO = "repository { isPrivate } contributions { totalCount }"


def fetch(token, login, full):
    this_year = dt.date.today().year
    years = list(range(this_year - 3, this_year))
    per_year = "\n".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
        f"{{ contributionCalendar {{ totalContributions }} }}" for y in years)
    q = f"""
    query($login: String!) {{
      user(login: $login) {{
        createdAt
        window: contributionsCollection {{
          hasAnyRestrictedContributions
          restrictedContributionsCount
          contributionCalendar {{ totalContributions weeks {{ contributionDays {{ date contributionCount }} }} }}
          commitContributionsByRepository(maxRepositories: 100) {{ {BY_REPO} }}
          issueContributionsByRepository(maxRepositories: 100) {{ {BY_REPO} }}
          pullRequestContributionsByRepository(maxRepositories: 100) {{ {BY_REPO} }}
          pullRequestReviewContributionsByRepository(maxRepositories: 100) {{ {BY_REPO} }}
          repositoryContributions(first: 100) {{ nodes {{ repository {{ isPrivate }} }} }}
        }}
        {per_year}
      }}
    }}"""
    u = graphql(token, q, {"login": login})["user"]
    if u is None:
        raise SystemExit(f"GitHub API: no user {login}")
    w = u["window"]
    cal = w["contributionCalendar"]
    days = sorted((d["date"], d["contributionCount"]) for wk in cal["weeks"] for d in wk["contributionDays"])
    if len(days) < WEEKS * 7:
        raise SystemExit(f"calendar too short: {len(days)} days")

    # Private = contributions the viewer cannot see (the calendar shares them anonymously)
    # plus any visible ones that sit in private repos.
    private = w["restrictedContributionsCount"]
    for key in ("commit", "issue", "pullRequest", "pullRequestReview"):
        private += sum(r["contributions"]["totalCount"] for r in w[f"{key}ContributionsByRepository"]
                       if r["repository"]["isPrivate"])
    private += sum(1 for node in w["repositoryContributions"]["nodes"] if node["repository"]["isPrivate"])

    created = int(u["createdAt"][:4])
    data = dict(
        login=login,
        total=cal["totalContributions"],
        private=private if w["hasAnyRestrictedContributions"] or private else None,
        days=days,
        years=[(y, u[f"y{y}"]["contributionCalendar"]["totalContributions"]) for y in years if y >= created],
        merged=None,
    )
    if full:
        q = """
        query($login: String!, $priv: String!) {
          user(login: $login) { pullRequests(states: MERGED) { totalCount } }
          priv: search(type: ISSUE, query: $priv, first: 0) { issueCount }
        }"""
        base = f"author:{login} is:pr is:merged"
        r = graphql(token, q, {"login": login, "priv": base + " is:private"})
        merged, merged_priv = r["user"]["pullRequests"]["totalCount"], r["priv"]["issueCount"]
        if merged_priv > 0:
            data["merged"] = (merged, merged_priv)
        else:
            print("STATS_TOKEN sees no merged PRs in private repos; leaving the merged-PR total out.")
    return data


def derive(d):
    """Everything the panel draws, computed from the raw counts."""
    days = d["days"][-WEEKS * 7:]
    counts = [c for _, c in days]
    bins = [sum(counts[i * 7:(i + 1) * 7]) for i in range(WEEKS)]
    start = dt.date.fromisoformat(days[0][0])
    end = dt.date.fromisoformat(days[-1][0])
    window_start = dt.date.fromisoformat(d["days"][0][0])
    # compare against the latest calendar year that lies wholly before the 12-month window
    cmp = next(((y, v) for y, v in reversed(d["years"]) if y < window_start.year and v > 0), None)
    return dict(
        d,
        bins=bins,
        start=start,
        end=end,
        active_weeks=sum(1 for b in bins if b),
        active_days=sum(1 for c in counts if c),
        n_days=len(counts),
        cmp=cmp,
    )


# ---------------------------------------------------------------- drawing helpers

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(s, fs, ls=0.0):
    """Approximate rendered width of a monospace string."""
    return len(s) * (ADV * fs + ls)


def n(v):
    return f"{v:,}"


def pct(a, b):
    return f"{round(100 * a / b)}%" if b else "0%"


def growth(v, base):
    r = v / base
    return f"×{r:.0f}" if r >= 10 else f"×{r:.1f}"


def nice_step(x):
    """Smallest 1-2-5 step >= x."""
    m = 1
    while True:
        for s in (1, 2, 5):
            if s * m >= x:
                return s * m
        m *= 10


def chrome(c, W, bar_h, title, fs):
    dots = "".join(f'<circle cx="{18 + i * 14}" cy="{bar_h / 2}" r="4" fill="{c["dim"]}"/>' for i in range(3))
    return (f'<rect x=".5" y=".5" width="{W - 1}" height="{bar_h}" rx="9.5" fill="{c["bar"]}"/>'
            f'<rect x=".5" y="{bar_h - 9.5}" width="{W - 1}" height="10" fill="{c["bar"]}"/>'
            f'<path d="M.5 {bar_h + .5}H{W - .5}" stroke="{c["border"]}"/>'
            f'{dots}<text x="{W / 2}" y="{bar_h / 2 + fs * .35:.1f}" text-anchor="middle" font-size="{fs}" fill="{c["muted"]}">{title}</text>')


def style():
    return f"""<style>
text{{font-family:{MONO};}}
.live{{transform-box:fill-box;transform-origin:center;animation:ping 2.4s ease-out infinite;}}
@keyframes ping{{0%{{transform:scale(1);opacity:.9}}70%,100%{{transform:scale(3.4);opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.live{{animation:none;opacity:0}}}}
</style>"""


def scope(c, d, uid, x0, y0, w, h, cols, rows, month_every, fs):
    """Weekly totals as a trace with filled area on an oscilloscope graticule."""
    bins = d["bins"]
    peak = max(bins)
    per_div = nice_step(peak / (rows * 0.95)) if peak else 1
    full = per_div * rows
    cw, rh, ww = w / cols, h / rows, w / WEEKS
    yb = y0 + h
    out = []

    grid = "".join(f"M{x0 + i * cw:g} {y0}V{yb}" for i in range(1, cols))
    grid += "".join(f"M{x0} {y0 + j * rh:g}H{x0 + w}" for j in range(1, rows))
    out.append(f'<path d="{grid}" stroke="{c["major"]}" stroke-width="1"/>')
    ticks = "".join(f"M{x0 + k * ww:.1f} {yb - 3}V{yb}" for k in range(1, WEEKS))
    out.append(f'<path d="{ticks}" stroke="{c["axis"]}" stroke-width="1"/>')
    out.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="{c["axis"]}" stroke-width="1"/>')

    xs = [x0 + (i + .5) * ww for i in range(WEEKS)]
    ys = [yb - v / full * h for v in bins]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in zip(xs, ys))
    out.append(f'<path d="{line} L{xs[-1]:.1f} {yb} L{xs[0]:.1f} {yb}Z" fill="url(#{uid}fill)"/>')

    # max-hold cursor at the real peak; its label goes on the side where the trace sits lower
    if peak:
        yp = yb - peak / full * h
        out.append(f'<path d="M{x0} {yp:.1f}H{x0 + w}" stroke="{c["muted"]}" stroke-opacity=".6" stroke-width="1" stroke-dasharray="2 3"/>')
        label = f"max {n(peak)}/wk"
        lw = tw(label, fs)
        left = max(v for x, v in zip(xs, bins) if x < x0 + 8 + lw + 6)
        right = max(v for x, v in zip(xs, bins) if x > x0 + w - 8 - lw - 6)
        lx, anchor = (x0 + 6, "start") if left <= right else (x0 + w - 6, "end")
        out.append(f'<text x="{lx}" y="{yp + fs + 3:.1f}" font-size="{fs}" fill="{c["muted"]}" text-anchor="{anchor}">{label}</text>')

    out.append(f'<path d="{line}" fill="none" stroke="{c["accent"]}" stroke-width="1.75" stroke-linejoin="round" stroke-linecap="round"/>')
    out.append(f'<circle class="live" cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="2.75" fill="none" stroke="{c["accent"]}" stroke-width="1.25"/>'
               f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="2.75" fill="{c["accent"]}"/>')

    # month ticks below the frame; January carries the year
    labels, mt = [], []
    day_w = w / d["n_days"]
    m = dt.date(d["start"].year, d["start"].month, 1)
    while m <= d["end"]:
        if m > d["start"] and (m.month - 1) % month_every == 0:
            x = x0 + (m - d["start"]).days * day_w
            text, fill = (str(m.year), c["text"]) if m.month == 1 else (MONTHS[m.month - 1], c["muted"])
            if x + 3 + tw(text, fs) <= x0 + w:
                mt.append(f"M{x:.1f} {yb}V{yb + 4}")
                labels.append(f'<text x="{x + 3:.1f}" y="{yb + fs + 5}" font-size="{fs}" fill="{fill}">{text}</text>')
        m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    out.append(f'<path d="{"".join(mt)}" stroke="{c["axis"]}" stroke-width="1"/>')
    out.extend(labels)

    defs = (f'<linearGradient id="{uid}fill" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="{c["accent"]}" stop-opacity="{c["fill"]}"/>'
            f'<stop offset="1" stop-color="{c["accent"]}" stop-opacity=".02"/></linearGradient>')
    return "".join(out), defs, per_div


def bars(c, items, x_right, yb, hmax, bw, gap, fs):
    """Per-year totals as small bars, right-aligned at x_right; the last bar is the 12-month window."""
    vmax = max(v for _, v in items) or 1
    x = x_right - len(items) * bw - (len(items) - 1) * gap
    out = []
    for i, (lab, v) in enumerate(items):
        last = i == len(items) - 1
        bh = max(1.0, v / vmax * hmax) if v else 0
        cx = x + bw / 2
        out.append(f'<rect x="{x:.1f}" y="{yb - bh:.1f}" width="{bw}" height="{bh:.1f}" fill="{c["accent"] if last else c["raw"]}"'
                   f'{"" if last else " fill-opacity=\".55\""}/>')
        out.append(f'<text x="{cx:.1f}" y="{yb - bh - 4:.1f}" font-size="{fs}" text-anchor="middle" fill="{c["text"]}" fill-opacity=".82">{n(v)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{yb + fs + 4}" font-size="{fs}" text-anchor="middle" fill="{c["accent"] if last else c["muted"]}">{lab}</text>')
        x += bw + gap
    out.append(f'<path d="M{x_right - len(items) * bw - (len(items) - 1) * gap - 4:.1f} {yb + .5}H{x_right + 4}" stroke="{c["axis"]}"/>')
    return "".join(out)


def cell(c, x, x_end, label, idx, value, trail, caption, s):
    """One metric cell, laid out like the Shipped card."""
    out = [f'<text x="{x}" y="{s["ly"]}" font-size="{s["lfs"]}" fill="{c["muted"]}" letter-spacing=".1em">{esc(label)}</text>',
           f'<text x="{x_end}" y="{s["ly"]}" font-size="{s["lfs"]}" fill="{c["dim"]}" text-anchor="end">{idx:02d}</text>']
    t = f'<tspan fill="{c["accent"]}" font-weight="600">{esc(value)}</tspan>'
    if trail:
        t += f'<tspan fill="{c["muted"]}" font-size="{s["tfs"]}" dx="{s["tfs"] * .6:.1f}">{esc(trail)}</tspan>'
    out.append(f'<text x="{x}" y="{s["vy"]}" font-size="{s["vfs"]}">{t}</text>')
    out.append(f'<text x="{x}" y="{s["cy"]}" font-size="{s["cfs"]}" fill="{c["text"]}" fill-opacity=".82">{esc(caption)}</text>')
    return "".join(out)


# ---------------------------------------------------------------- panel

def metrics(d):
    """Small cells after the trajectory, in priority order; the merged-PR cell only when it can be trusted."""
    out = []
    if d["merged"]:
        total, priv = d["merged"]
        out.append(("MERGED PRS", n(total), "all-time", f"{pct(priv, total)} in private repos"))
    out.append(("ACTIVE WEEKS", str(d["active_weeks"]), f"/ {WEEKS}", "in the last 12 mo"))
    out.append(("ACTIVE DAYS", str(d["active_days"]), f"/ {d['n_days']}", f"{pct(d['active_days'], d['n_days'])} of days"))
    return out[:2]


def describe(d):
    parts = [f"{n(d['total'])} contributions in the last 12 months"]
    if d["private"] is not None:
        parts[0] += f", {pct(d['private'], d['total'])} of them in private repos"
    parts.append(f"weekly contributions peaked at {n(max(d['bins']))}")
    yrs = ", ".join(f"{y}: {n(v)}" for y, v in d["years"])
    s = f"contributions per year: {yrs}, last 12 months: {n(d['total'])}"
    if d["cmp"]:
        s += f" ({growth(d['total'], d['cmp'][1])} vs {d['cmp'][0]})"
    parts.append(s)
    if d["merged"]:
        parts.append(f"{n(d['merged'][0])} merged pull requests all-time")
    parts.append(f"active in {d['active_weeks']} of the last {WEEKS} weeks")
    parts.append(f"updated {d['end'].isoformat()} from the GitHub GraphQL API")
    return "; ".join(parts) + "."


def panel(d, theme, narrow):
    c = THEMES[theme]
    uid = f"t{theme[0]}{'n' if narrow else 'w'}"
    if not narrow:
        W, bar, tfs = 860, 32, 11
        L, R = 40, 820
        py, pfs = 70, 15
        hy, hnfs, hfs = 116, 34, 17
        ry, rfs = 146, 10
        sc = dict(x0=40, y0=156, w=780, h=120, cols=26, rows=4, month_every=1, fs=10)
        wk_div = "2 wk/div"
        div_y = 306
        s = dict(ly=332, lfs=10.5, vy=370, vfs=30, tfs=14, cy=393, cfs=12)
        H = 412
    else:
        W, bar, tfs = 340, 28, 10
        L, R = 16, 324
        py, pfs = 58, 13
        hy, hnfs, hfs = 96, 28, 13
        ry, rfs = 144, 10
        sc = dict(x0=14, y0=152, w=312, h=96, cols=13, rows=4, month_every=2, fs=10)
        wk_div = "4 wk/div"
        div_y = 280
        s = dict(ly=302, lfs=10, vy=336, vfs=24, tfs=11.5, cy=357, cfs=11)
        H = 478

    body, sdefs, per_div = scope(c, d, uid, **sc)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="{uid}t {uid}d">',
        f'<title id="{uid}t">Telemetry: GitHub activity, last 12 months</title>',
        f'<desc id="{uid}d">{esc(describe(d))}</desc>',
        style(),
        f"<defs>{sdefs}</defs>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="9.5" fill="{c["bg"]}" stroke="{c["border"]}"/>',
        chrome(c, W, bar, "~/GabeMed", tfs),
        f'<text x="{L}" y="{py}" font-size="{pfs}" fill="{c["text"]}"><tspan fill="{c["accent"]}">$</tspan> gh telemetry --window 12mo</text>',
        f'<text x="{R}" y="{py}" font-size="{10 if narrow else 11}" fill="{c["muted"]}" text-anchor="end">{"" if narrow else "updated "}{d["end"].isoformat()}</text>',
    ]

    # headline
    share = None if d["private"] is None else pct(d["private"], d["total"])
    num = f'<tspan fill="{c["accent"]}" font-size="{hnfs}" font-weight="600">{n(d["total"])}</tspan>'
    if not narrow:
        rest = f'<tspan dx="{hfs * .6:.1f}">contributions</tspan>'
        if share:
            rest += (f'<tspan fill="{c["muted"]}"> · </tspan><tspan fill="{c["accent"]}" font-weight="600">{share}</tspan>'
                     f'<tspan> in private repos</tspan>')
        out.append(f'<text x="{L}" y="{hy}" font-size="{hfs}" fill="{c["text"]}">{num}{rest}</text>')
    else:
        out.append(f'<text x="{L}" y="{hy}" font-size="{hfs}" fill="{c["text"]}">{num}<tspan dx="{hfs * .6:.1f}">contributions</tspan></text>')
        if share:
            out.append(f'<text x="{L}" y="{hy + 22}" font-size="{hfs}" fill="{c["text"]}"><tspan fill="{c["accent"]}" font-weight="600">{share}</tspan> in private repos</text>')

    # scope readout
    out.append(f'<g font-size="{rfs}" fill="{c["muted"]}" letter-spacing=".04em">'
               f'<text x="{sc["x0"]}" y="{ry}">contributions / week</text>'
               f'<text x="{sc["x0"] + sc["w"]}" y="{ry}" text-anchor="end">{n(per_div)}/div · {wk_div}</text></g>')
    out.append(body)
    out.append(f'<path d="M.5 {div_y + .5}H{W - .5}" stroke="{c["border"]}"/>')

    # trajectory + metric cells
    items = [(str(y), v) for y, v in d["years"]] + [("12 mo", d["total"])]
    value, trail = (growth(d["total"], d["cmp"][1]), f"vs {d['cmp'][0]}") if d["cmp"] else (n(d["total"]), "")
    cells = metrics(d)
    if not narrow:
        out.append(cell(c, L, 408, "CONTRIBUTIONS / YEAR", 1, value, trail, "trailing 12 mo, all repos", s))
        out.append(bars(c, items, 408, 384, 32, 30, 14, 10))
        for i, (lab, v, t, cap) in enumerate(cells):
            x = 430 + i * 195
            out.append(f'<path d="M{x + .5} {div_y + 14}V{H - 14}" stroke="{c["border"]}"/>')
            out.append(cell(c, x + 20, R if i == len(cells) - 1 else x + 175, lab, i + 2, v, t, cap, s))
    else:
        out.append(cell(c, L, R, "CONTRIBUTIONS / YEAR", 1, value, trail, "trailing 12 mo", s))
        out.append(bars(c, items, R - 4, 350, 28, 22, 9, 9.5))
        s2 = dict(s, ly=s["ly"] + 104, vy=s["vy"] + 104, cy=s["cy"] + 104)
        out.append(f'<path d="M12 {div_y + 94.5}H328" stroke="{c["border"]}"/>')
        out.append(f'<path d="M170.5 {div_y + 106}V{H - 12}" stroke="{c["border"]}"/>')
        for i, (lab, v, t, cap) in enumerate(cells):
            x = L if i == 0 else 184
            out.append(cell(c, x, 156 if i == 0 else R, lab, i + 2, v, t, cap, s2))
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER") or "GabeMed")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "telemetry"))
    a = ap.parse_args()

    stats = os.environ.get("STATS_TOKEN", "").strip()
    token = stats or os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise SystemExit("set STATS_TOKEN or GITHUB_TOKEN")
    print(f"token: {'STATS_TOKEN' if stats else 'GITHUB_TOKEN (public numbers only)'}")

    d = derive(fetch(token, a.user, full=bool(stats)))
    if d["total"] <= 0 or not any(d["bins"]):
        raise SystemExit("no contributions returned; keeping the existing SVGs")

    os.makedirs(a.out, exist_ok=True)
    for theme in ("dark", "light"):
        for narrow in (False, True):
            name = f"telemetry-{theme}{'-narrow' if narrow else ''}.svg"
            with open(os.path.join(a.out, name), "w", encoding="utf-8") as f:
                f.write(panel(d, theme, narrow))
    print(describe(d))
    print(f"wrote 4 SVGs to {os.path.relpath(a.out, ROOT)}")


if __name__ == "__main__":
    main()
