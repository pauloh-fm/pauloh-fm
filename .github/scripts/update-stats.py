#!/usr/bin/env python3
"""Gera bloco de 'coding languages' no README (estilo WakaTime) com dados reais
da API do GitHub (bytes por linguagem em todos os repos). Roda local ou no Action."""
import json, os, re, urllib.request

USER = "pauloh-fm"
REPO_PATH = os.environ.get("REPO_PATH", os.getcwd())
README = os.path.join(REPO_PATH, "README.md")

def api(path):
    token = os.environ.get("INPUT_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(f"https://api.github.com{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stats-generator")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def human_bytes(n):
    if n >= 1024 * 1024:
        return f"{n/1024/1024:.1f} MB".replace(".", ",")
    if n >= 1024:
        return f"{n/1024:.0f} KB"
    return f"{n} B"

def build_block():
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner")
    langs = {}
    for r in repos:
        try:
            l = api(f"/repos/{USER}/{r['name']}/languages")
        except Exception:
            continue
        for lang, bytes_ in l.items():
            langs[lang] = langs.get(lang, 0) + bytes_
    if not langs:
        return None
    top = sorted(langs.items(), key=lambda kv: -kv[1])
    if len(top) > 6:
        others = sum(v for _, v in top[6:])
        top = top[:6] + [("Other", others)]
    total = sum(langs.values())
    lines = []
    for lang, bytes_ in top:
        pct = bytes_ / total * 100
        filled = round(pct / 100 * 24)
        bar = "█" * filled + "░" * (24 - filled)
        lines.append(f"{lang:<16} {human_bytes(bytes_):>9}     {bar}   {pct:5.2f} %")
    block = (
        "<!-- STATS_START -->\n"
        "```text\n" + "\n".join(lines) + "\n```\n"
        "<!-- STATS_END -->"
    )
    print(block)
    return block, {k: v for k, v in top}

def main():
    block = build_block()
    if not block:
        print("sem dados", file=sys.stderr)
        sys.exit(1)
    block, _ = block
    with open(README) as f:
        readme = f.read()
    pattern = re.compile(r"<!-- STATS_START -->.*?<!-- STATS_END -->", re.S)
    if pattern.search(readme):
        readme = pattern.sub(lambda _: block, readme)
    else:
        # insere após o cabeçalho "## ? GitHub stats|Coding languages"
        m = re.search(r"^## .*?stats.*?$", readme, re.M | re.I)
        if m:
            end = m.end()
            readme = readme[:end] + "\n\n" + block + readme[end:]
        else:
            print("marcador e seção não encontrados", file=sys.stderr)
            sys.exit(1)
    with open(README, "w") as f:
        f.write(readme)
    print("README atualizado")

if __name__ == "__main__":
    import sys
    main()