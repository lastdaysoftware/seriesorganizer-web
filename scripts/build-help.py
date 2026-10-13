#!/usr/bin/env python3
"""Render reader-facing help using the site's existing News chrome."""
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
news = runpy.run_path(str(ROOT / "scripts" / "build-news.py"))
translations = {
    "Language and help": "Idioma e ajuda",
    "Series Organizer+ home": "Início do Series Organizer+",
    "Main navigation": "Navegação principal", "Footer navigation": "Navegação do rodapé",
    "Language": "Idioma", ">Features<": ">Funcionalidades<",
    ">Discover<": ">Descobrir<", ">News<": ">Notícias<", ">Help<": ">Ajuda<",
    ">Our story<": ">A nossa história<", ">What's next<": ">O que vem a seguir<",
    ">Privacy<": ">Privacidade<", ">Website Privacy<": ">Privacidade do website<",
    ">Account deletion<": ">Eliminar a conta<", ">Support<": ">Suporte<",
    ">Support us!<": ">Apoie-nos!<",
    "A LastDay Software project.": "Um projeto da LastDay Software.",
    "This product uses the TMDB API but is not endorsed or certified by TMDB.":
        "Este produto usa a API do TMDB mas não é apoiado nem certificado pela TMDB.",
    "Visit TMDB": "Visitar TMDB",
}

def chrome(prefix, portuguese=False):
    header, footer = news["header"](prefix), news["footer"](prefix)
    language = (f'<span><a href="{prefix}help/">EN</a> | <strong>PT</strong></span>'
                if portuguese else
                f'<span><strong>EN</strong> | <a href="{prefix}pt/help/">PT</a></span>')
    header = re.sub(r'<span><strong>EN</strong> \| <a href="[^"]+">PT</a></span>',language,header)
    if portuguese:
        for name in ("index.html", "privacy.html", "website-privacy.html", "account-deletion.html", "support.html"):
            header = header.replace(f'href="{prefix}{name}', f'href="{prefix}pt/{name}')
            footer = footer.replace(f'href="{prefix}{name}', f'href="{prefix}pt/{name}')
        header = header.replace(f'href="{prefix}help/"',f'href="{prefix}pt/help/"')
        # The EN language link stays at the English Help counterpart.
        header = header.replace(f'<a href="{prefix}pt/help/">EN</a>', f'<a href="{prefix}help/">EN</a>')
        footer = footer.replace(f'href="{prefix}help/"',f'href="{prefix}pt/help/"')
        for original, translated in translations.items():
            header, footer = header.replace(original,translated), footer.replace(original,translated)
    return header, footer

pages = (
    ("help/index.html", "en", "Help and guides", "Get help with your Library, sync, backups and Browser Watching.", "en.html", "../"),
    ("pt/help/index.html", "pt-PT", "Ajuda e guias", "Ajuda com a Biblioteca, sincronização, backups e Browser Watching.", "pt.html", "../../"),
    ("guides/library-sync-backup.html", "en", "Library, sync and cloud backups", "Understand Library updates, account sync, automatic sync, backups and restore.", "library-sync-backup.html", "../"),
)
for target, lang, title, description, source, prefix in pages:
    canonical_path = target.removesuffix("index.html")
    head = news["document_head"](title,description,f'https://seriesorganizer.com/{canonical_path}',prefix)
    if target.endswith("help/index.html"):
        head += '\n<link rel="alternate" hreflang="en" href="https://seriesorganizer.com/help/" />'
        head += '\n<link rel="alternate" hreflang="pt-PT" href="https://seriesorganizer.com/pt/help/" />'
        head += '\n<link rel="alternate" hreflang="x-default" href="https://seriesorganizer.com/help/" />'
    header, footer = chrome(prefix,lang=="pt-PT")
    body = (ROOT / "content" / "help" / source).read_text(encoding="utf-8")
    output = f'<!doctype html>\n<html lang="{lang}">\n<head>\n{head}\n</head>\n<body>\n{header}\n<main class="policy-page"><div class="container policy-container help-article">\n{body}\n</div></main>\n{footer}\n</body></html>\n'
    path = ROOT / target
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(output,encoding="utf-8")
print(f"Built {len(pages)} reader-facing help pages.")
