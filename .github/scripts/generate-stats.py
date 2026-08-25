#!/usr/bin/env python3
"""Gera stats.svg com dados reais do GitHub (REST + GraphQL).
Funciona local (gh token) e no GitHub Actions (GITHUB_TOKEN)."""
import json, os, sys, urllib.request

USER = "pauloh-fm"

def api(path):
    token = os.environ.get("INPUT_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(f"https://api.github.com{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stats-generator")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def api_graphql(query):
    token = os.environ.get("INPUT_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "stats-generator"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

# Cores por linguagem (linguist)
LANG_COLORS = {
    "C": "#555555", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "CMake": "#DA3434", "Jupyter Notebook": "#DA5B0B", "CSS": "#563d7c",
    "HTML": "#e34c26", "Shell": "#89e051", "TypeScript": "#3178c6",
    "Java": "#b07219", "Ruby": "#701516", "Go": "#00ADD8",
    "Others": "#8e8e8e",
}

def main():
    u = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    stars = sum(r.get("stargazers_count") or 0 for r in repos)
    langs = {}
    for r in repos:
        lang = r.get("language") or "Others"
        langs[lang] = langs.get(lang, 0) + 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    total = sum(c for _, c in top)

    contrib = None
    q = '{ user(login:"%s") { contributionsCollection { contributionCalendar { totalContributions } } } }' % USER
    try:
        g = api_graphql(q)
        contrib = g["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception:
        pass

    repo_count, followers, following = u.get("public_repos", 0), u.get("followers", 0), u.get("following", 0)
    contrib_txt = f"{contrib:,}".replace(",", ".") if contrib is not None else "—"
    name = u.get("name") or USER

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    W, PAD = 495, 24
    # barras de linguagens
    bar_y = 182
    bar_rows = []
    for i, (lang, count) in enumerate(top):
        pct = count / total * 100 if total else 0
        y = bar_y + i * 24
        bar_rows.append(f'''
  <text x="{PAD}" y="{y+12}" fill="#cfe9f5" font-size="13">{esc(lang)}</text>
  <rect x="120" y="{y+2}" width="250" height="12" rx="6" fill="#16374a"/>
  <rect x="120" y="{y+2}" width="{250*pct/100:.1f}" height="12" rx="6" fill="{LANG_COLORS.get(lang, '#38bdf8')}"/>
  <text x="388" y="{y+12}" fill="#9ad0e8" font-size="12">{pct:.1f}%</text>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="290" viewBox="0 0 {W} 290" font-family="Segoe UI, -apple-system, Arial, sans-serif">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10232e"/>
      <stop offset="100%" stop-color="#0a171f"/>
    </linearGradient>
    <linearGradient id="ph" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0e7490"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{W-2}" height="288" rx="12" fill="url(#bg)" stroke="#2b5a70" stroke-width="1"/>
  <rect x="1" y="1" width="{W-2}" height="6" rx="3" fill="#38bdf8"/>

  <!-- header -->
  <circle cx="56" cy="56" r="24" fill="url(#ph)"/>
  <text x="56" y="62" text-anchor="middle" fill="#ffffff" font-size="20" font-weight="700">{esc(name[:2].upper())}</text>
  <text x="92" y="52" fill="#ffffff" font-size="17" font-weight="700">{esc(name)}</text>
  <text x="92" y="70" fill="#7fb8d4" font-size="12">@{esc(USER)}</text>

  <!-- metricas -->
  <g>
    <path d="M10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-8l-2-2z" fill="#38bdf8" transform="translate(24,88) scale(1.15)"/>
    <path d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" fill="#f1c40f" transform="translate(150,88) scale(1.15)"/>
    <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" fill="#4ade80" transform="translate(276,88) scale(1.15)"/>
    <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" fill="#e879f9" transform="translate(402,88) scale(1.15)"/>
  </g>
  <g>
    <text x="24"  y="133" fill="#ffffff" font-size="24" font-weight="700">{repo_count}</text>
    <text x="150" y="133" fill="#ffffff" font-size="24" font-weight="700">{stars}</text>
    <text x="276" y="133" fill="#ffffff" font-size="24" font-weight="700">{followers}</text>
    <text x="402" y="133" fill="#ffffff" font-size="22" font-weight="700">{contrib_txt}</text>
  </g>
  <g fill="#7fb8d4" font-size="11">
    <text x="24"  y="150">Repos</text>
    <text x="150" y="150">Stars</text>
    <text x="276" y="150">Followers</text>
    <text x="402" y="150">1-yr contrib</text>
  </g>

  <line x1="{PAD}" y1="168" x2="{W-PAD}" y2="168" stroke="#1c3d50" stroke-width="1"/>
  <text x="{PAD}" y="176" fill="#38bdf8" font-size="12" font-weight="600" letter-spacing="1">TOP LANGUAGES</text>
{''.join(bar_rows)}
</svg>'''
    with open("stats.svg", "w") as f:
        f.write(svg)
    print(f"stats.svg gerado ({len(svg)} bytes): repos={repo_count} stars={stars} followers={followers} contrib={contrib_txt}")
    print("top:", top)

if __name__ == "__main__":
    main()