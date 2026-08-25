#!/usr/bin/env python3
"""Gera stats.svg com dados reais do GitHub via API (REST + GraphQL).
Funciona localmente (gh/curl com token) e no GitHub Actions (GITHUB_TOKEN)."""
import json, os, subprocess, sys, urllib.request

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

def main():
    try:
        u = api(f"/users/{USER}")
    except Exception as e:
        print(f"FALHA API: {e}", file=sys.stderr)
        sys.exit(1)
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    stars = sum(r.get("stargazers_count") or 0 for r in repos)
    langs = {}
    for r in repos:
        lang = r.get("language") or "Others"
        langs[lang] = langs.get(lang, 0) + 1
    top_langs = sorted(langs.items(), key=lambda kv: -kv[1])[:5]

    contrib = None
    q = '{ user(login:"%s") { contributionsCollection { contributionCalendar { totalContributions } } } }' % USER
    try:
        g = api_graphql(q)
        contrib = g["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception:
        pass

    repo_count = u.get("public_repos", 0)
    followers = u.get("followers", 0)
    following = u.get("following", 0)
    gists = u.get("public_gists", 0)

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lang_line = "   ".join(f"{esc(n)} {c}" for n, c in top_langs) if top_langs else "—"
    contrib_txt = f"{contrib:,}".replace(",", ".") if contrib is not None else "—"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="240" viewBox="0 0 495 240" font-family="Segoe UI, -apple-system, Arial, sans-serif">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#003d5c"/>
      <stop offset="100%" stop-color="#005f8c"/>
    </linearGradient>
  </defs>
  <rect width="495" height="240" rx="10" fill="url(#g)"/>
  <rect x="0" y="0" width="495" height="5" fill="#38bdf8"/>
  <text x="24" y="38" fill="#38bdf8" font-size="15" font-weight="600" letter-spacing="1">GITHUB STATS</text>
  <text x="24" y="66" fill="#ffffff" font-size="22" font-weight="700">@{esc(USER)}</text>
  <text x="24" y="88" fill="#9ad0e8" font-size="12">{esc(u.get("name") or "")}</text>

  <g font-size="26" font-weight="700" fill="#ffffff">
    <text x="24"   y="135">{repo_count}</text>
    <text x="150"  y="135">{followers}</text>
    <text x="276"  y="135">{stars}</text>
    <text x="402"  y="135">{contrib_txt}</text>
  </g>
  <g font-size="11" fill="#9ad0e8">
    <text x="24"   y="155">Repos</text>
    <text x="150"  y="155">Followers</text>
    <text x="276"  y="155">Stars</text>
    <text x="402"  y="155">1-yr contrib</text>
  </g>

  <line x1="24" y1="172" x2="471" y2="172" stroke="#1c7fae" stroke-width="1"/>
  <text x="24" y="194" fill="#9ad0e8" font-size="11">Top languages</text>
  <text x="24" y="216" fill="#ffffff" font-size="13" font-weight="600">{esc(lang_line)}</text>
</svg>'''
    out = "stats.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"stats.svg gerado: repos={repo_count} followers={followers} stars={stars} contrib={contrib_txt} langs={top_langs}")
    print(f"ARQUIVO={out} bytes={len(svg)}")

if __name__ == "__main__":
    main()