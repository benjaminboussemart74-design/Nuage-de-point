"""
Enregistre une vidéo de démonstration du simulateur pour LinkedIn (format vertical 4:5, 1080 × 1350).

Le script ouvre la page dans un navigateur sans écran, joue un parcours de visiteur
(scénarios, curseurs, courbes) avec un curseur visible et des légendes à l'écran.
Chaque image affichée est capturée par le protocole de débogage de Chromium (« screencast »)
avec son horodatage, puis ffmpeg assemble ces images en MP4 lisible par LinkedIn.

Utilisation :
    python scripts/video_linkedin.py
Sortie : videos/simulateur_linkedin.mp4 et videos/couverture_linkedin.png
Avec l'option --court : videos/simulateur_linkedin_30s.mp4, une version de 30 secondes environ.
"""

import asyncio
import base64
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.async_api import async_playwright

RACINE = Path(__file__).resolve().parent.parent
PAGE = (RACINE / "cohortes-presidentielle" / "index.html").as_uri()
SORTIE = RACINE / "videos"
CHROMIUM = "/opt/pw-browsers/chromium"

# Format vertical 4:5 : la page est affichée en 540 × 675 points, rendue deux fois plus fine.
LARGEUR, HAUTEUR, ECHELLE = 540, 675, 2

# Version courte : même parcours resserré, attentes raccourcies.
COURT = "--court" in sys.argv
RYTHME = 0.6 if COURT else 1.0

# Habillage de la vidéo : légende en haut de l'écran, curseur visible, cartes de titre.
HABILLAGE_CSS = """
#video-legende { position: fixed; left: 12px; right: 12px; top: 58px; z-index: 50; padding: 10px 14px;
  background: var(--text); color: var(--bg); font: 600 16px/1.35 'DM Sans', sans-serif;
  border-left: 4px solid var(--red); transition: opacity 0.25s; }
#video-legende[hidden] { display: block !important; opacity: 0; }
#video-curseur { position: fixed; z-index: 60; width: 22px; height: 22px; margin: -11px 0 0 -11px; border-radius: 50%;
  background: rgba(176, 30, 40, 0.35); border: 2px solid #B01E28; pointer-events: none;
  transition: left 0.6s cubic-bezier(0.22, 1, 0.36, 1), top 0.6s cubic-bezier(0.22, 1, 0.36, 1), transform 0.15s; }
#video-curseur.clic { transform: scale(0.7); }
#video-carte { position: fixed; inset: 0; z-index: 70; background: var(--bg); display: flex; flex-direction: column;
  justify-content: center; gap: 18px; padding: 0 36px; transition: opacity 0.4s; }
#video-carte[hidden] { display: flex !important; opacity: 0; pointer-events: none; }
#video-carte .filet-carte { width: 64px; height: 4px; background: var(--red); }
#video-carte h1 { font-size: 1.95rem; line-height: 1.12; }
#video-carte p { font-size: 17px; color: var(--text-secondary); margin: 0; line-height: 1.5; }
#video-carte .petit { font-size: 12px; color: var(--text-muted); }
#video-carte .grand { font-family: var(--font-serif); font-size: 1.55rem; line-height: 1.3; color: var(--text); font-weight: 700; letter-spacing: -0.01em; }
/* Dans la vidéo, les courbes tiennent dans la largeur de l'écran */
.figure-courbes svg.trace { min-width: 0 !important; }
"""


async def main():
    SORTIE.mkdir(exist_ok=True)
    brut = SORTIE / "brut"
    shutil.rmtree(brut, ignore_errors=True)

    async with async_playwright() as p:
        navigateur = await p.chromium.launch(executable_path=CHROMIUM)
        contexte = await navigateur.new_context(
            viewport={"width": LARGEUR, "height": HAUTEUR}, device_scale_factor=ECHELLE, color_scheme="light",
        )
        page = await contexte.new_page()
        await page.goto(PAGE)
        await page.wait_for_timeout(800)

        # Capture : Chromium envoie une image à chaque changement d'affichage, avec son horodatage.
        brut.mkdir(parents=True)
        images = []
        cdp = await contexte.new_cdp_session(page)

        async def recevoir(evenement):
            chemin = brut / f"{len(images):05d}.jpg"
            chemin.write_bytes(base64.b64decode(evenement["data"]))
            images.append((chemin, evenement["metadata"]["timestamp"]))
            await cdp.send("Page.screencastFrameAck", {"sessionId": evenement["sessionId"]})

        cdp.on("Page.screencastFrame", lambda e: asyncio.ensure_future(recevoir(e)))
        await page.add_style_tag(content=HABILLAGE_CSS)
        await page.evaluate("""() => {
          for (const [id, tag] of [['video-legende', 'div'], ['video-curseur', 'div'], ['video-carte', 'div']]) {
            const e = document.createElement(tag); e.id = id; document.body.appendChild(e);
          }
          document.getElementById('video-legende').hidden = true;
          document.getElementById('video-carte').hidden = true;
          const c = document.getElementById('video-curseur'); c.style.left = '270px'; c.style.top = '600px';
        }""")

        async def pause(secondes):
            await page.wait_for_timeout(int(secondes * 1000))

        async def temps(secondes):
            # Attente de mise en scène, raccourcie dans la version courte
            await pause(secondes * RYTHME)

        async def legende(texte):
            await page.evaluate("t => { const l = document.getElementById('video-legende'); l.textContent = t; l.hidden = !t; }", texte)

        async def carte(html):
            await page.evaluate("h => { const c = document.getElementById('video-carte'); c.innerHTML = h; c.hidden = !h; }", html)

        async def defiler(selecteur, marge=180):
            await page.evaluate("""([s, m]) => {
              const e = document.querySelector(s);
              window.scrollTo({ top: e.getBoundingClientRect().top + window.scrollY - m, behavior: 'smooth' });
            }""", [selecteur, marge])
            await temps(1.0)

        async def viser(selecteur):
            boite = await page.locator(selecteur).first.bounding_box()
            x, y = boite["x"] + boite["width"] / 2, boite["y"] + boite["height"] / 2
            await page.evaluate("([x, y]) => { const c = document.getElementById('video-curseur'); c.style.left = x + 'px'; c.style.top = y + 'px'; }", [x, y])
            await temps(0.7)
            return x, y

        async def cliquer(selecteur):
            # Sur téléphone, les scénarios défilent dans une rangée : on amène le bouton à l'écran.
            await page.evaluate("s => document.querySelector(s).scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })", selecteur)
            await pause(0.4)
            await viser(selecteur)
            await page.evaluate("() => document.getElementById('video-curseur').classList.add('clic')")
            await page.locator(selecteur).first.click()
            await pause(0.15)
            await page.evaluate("() => document.getElementById('video-curseur').classList.remove('clic')")

        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                                "maxWidth": LARGEUR * ECHELLE, "maxHeight": HAUTEUR * ECHELLE})

        async def glisser(i, de, a, pas_valeur=2):
            """Fait glisser le curseur de participation de la tranche i, avec le curseur visible."""
            await viser(f"#sim-p-{i}")
            sens = 1 if a >= de else -1
            for valeur in list(range(de, a, sens * pas_valeur)) + [a]:
                await page.evaluate("([i, v]) => { const e = document.getElementById('sim-p-' + i); e.value = v; e.dispatchEvent(new Event('input', { bubbles: true }));"
                                    " const c = document.getElementById('video-curseur'); const r = e.getBoundingClientRect(); c.style.left = (r.left + 12 + (r.width - 24) * v / 100) + 'px'; }", [i, valeur])
                await pause(0.05)

        async def choisir(i, valeur):
            """Change le menu « pour qui votent-ils » de la tranche i."""
            await viser(f"#sim-c-{i}")
            await page.evaluate("() => document.getElementById('video-curseur').classList.add('clic')")
            await page.evaluate("([i, v]) => { const e = document.getElementById('sim-c-' + i); e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); }", [i, valeur])
            await pause(0.15)
            await page.evaluate("() => document.getElementById('video-curseur').classList.remove('clic')")

        async def scenario(selecteur, question, reponse):
            """Choisit un scénario, puis montre le verdict et le podium."""
            await legende(question)
            await defiler("#scenarios")
            await cliquer(selecteur)
            await pause(0.4)
            await defiler("#sim-label", 150)
            await legende(reponse)
            await pause(3.0)

        if COURT:
            # Version de 30 secondes : un titre, un scénario par présidentielle, les réglages en direct, la fin.
            await carte("""<div class="filet-carte"></div>
          <h1>Jeunesse, vieillesse, abstention&nbsp;: comment l'abstention différenciée pèse-t-elle sur le résultat des élections&nbsp;?</h1>
          <p class="grand">Découvrez les effets possibles de la mobilisation de chaque génération.</p>""")
            await pause(3.6)
            await carte("")
            await legende("2022 : et si les 70 ans et plus étaient restés chez eux ?")
            await defiler(".scrutins", 170)
            await cliquer('.scrutins [data-sim-election="2022"]')
            await defiler("#scenarios")
            await cliquer('[data-scenario="sans-aines"]')
            await defiler("#sim-label", 150)
            await legende("Macron éliminé : Le Pen face à Mélenchon")
            await pause(2.6)
            await legende("2027 : et si les moins de 35 ans votaient comme les 75 ans et plus ?")
            await defiler(".scrutins", 170)
            await cliquer('.scrutins [data-sim-election="2027"]')
            await defiler("#scenarios")
            await cliquer('[data-scenario="jeunes-choisissent-aines"]')
            await defiler("#sim-label", 150)
            await legende("Philippe passe au second tour à la place de Mélenchon")
            await pause(2.6)
            await legende("À vous de régler chaque génération : le résultat suit en direct")
            await defiler("#scenarios")
            await cliquer('[data-scenario="reel"]')
            await defiler("#sim-ages", 175)
            await glisser(0, 68, 100, 4)
            await glisser(1, 69, 100, 4)
            await legende("Tous les jeunes votent : Mélenchon monte")
            await pause(1.6)
            await legende("Et s'ils votaient comme leurs grands-parents ?")
            await choisir(0, 5)
            await choisir(1, 5)
            await legende("Philippe repasse devant Mélenchon")
            await pause(2.2)
            await legende("")
            await carte("""<div class="filet-carte"></div>
          <h1>À vous de jouer</h1>
          <p class="grand">Faites voter ou s'abstenir chaque génération, et voyez qui passerait au second tour.</p>
          <p>Lien en commentaire.</p>
          <p class="petit">Sources : Odoxa-Backbone (octobre 2026) ; Ipsos, Sociologie des électorats 2022 ; INSEE ; ministère de l'Intérieur. Simulation à titre indicatif.</p>""")
            await pause(3.2)

        else:
            # 1. Vos mots, en cartes de texte
            await carte("""<div class="filet-carte"></div>
              <h1>Jeunesse, vieillesse, abstention&nbsp;: comment l'abstention différenciée pèse-t-elle sur le résultat des élections passées et à venir&nbsp;?</h1>""")
            await pause(4.0)
            await carte("""<div class="filet-carte"></div>
              <p class="grand">La fracture entre une jeunesse réputée progressiste et une vieillesse présentée comme conservatrice est un lieu commun de la science politique.</p>""")
            await pause(3.8)
            await carte("""<div class="filet-carte"></div>
              <p class="grand">À gauche comme à droite, les candidats ont volontiers bâti leur stratégie de campagne sur l'appel à l'une de ces fractions de l'électorat.</p>""")
            await pause(3.8)
            await carte("""<div class="filet-carte"></div>
              <p class="grand">Découvrez les effets possibles de la mobilisation de chaque génération.</p>""")
            await pause(2.4)
            await carte("")

            # 2. Présidentielle 2022 : les scénarios d'abstention
            await legende("Rejouez la présidentielle 2022")
            await defiler(".scrutins", 170)
            await cliquer('.scrutins [data-sim-election="2022"]')
            await pause(0.6)
            await scenario('[data-scenario="sans-aines"]',
                           "Scénario : et si les 70 ans et plus étaient restés chez eux ?",
                           "Emmanuel Macron éliminé : Marine Le Pen face à Jean-Luc Mélenchon")
            await scenario('[data-scenario="aines-comme-jeunes"]',
                           "Scénario : et si les 60 ans et plus votaient comme les 25-34 ans ?",
                           "Jean-Luc Mélenchon arrive en tête du premier tour")

            # 3. Présidentielle 2027 : le sondage d'octobre
            await legende("Et pour 2027 ? Le sondage Odoxa-Backbone, 12 005 personnes")
            await defiler(".scrutins", 170)
            await cliquer('.scrutins [data-sim-election="2027"]')
            await pause(0.3)
            await cliquer('[data-scenario="reel"]')
            await pause(0.4)
            await defiler("#sim-label", 150)
            await legende("Mélenchon devance Philippe d'un seul point pour le second tour")
            await pause(3.0)
            await scenario('[data-scenario="jeunes-choisissent-aines"]',
                           "Scénario : et si les moins de 35 ans votaient comme les 75 ans et plus ?",
                           "Édouard Philippe passe au second tour à la place de Mélenchon")

            # 4. Les réglages à la main : la barre du bas suit chaque geste
            await legende("À vous de régler chaque génération : le résultat suit en direct, en bas de l'écran")
            await defiler("#scenarios")
            await cliquer('[data-scenario="reel"]')
            await defiler("#sim-ages", 175)
            await pause(1.2)
            await glisser(0, 68, 100)
            await glisser(1, 69, 100)
            await legende("Tous les jeunes votent : Mélenchon monte à 20 %")
            await pause(2.6)
            await legende("Et s'ils votaient comme leurs grands-parents ?")
            await choisir(0, 5)
            await pause(0.8)
            await choisir(1, 5)
            await pause(0.6)
            await legende("Philippe repasse devant Mélenchon")
            await pause(3.0)

            # 5. Carte de fin
            await legende("")
            await carte("""<div class="filet-carte"></div>
              <h1>À vous de jouer</h1>
              <p class="grand">Faites voter ou s'abstenir chaque génération, en 2022, en 2024 et pour 2027, et voyez qui passerait au second tour.</p>
              <p>Lien en commentaire.</p>
              <p class="petit">Sources : Odoxa-Backbone, intentions de vote pour 2027 (octobre 2026) ; Ipsos, Sociologie des électorats 2022 et 2024 ; INSEE ; ministère de l'Intérieur. Simulation à titre indicatif.</p>""")
            await pause(4.0)

        # Image de couverture, prise sur la carte de titre
        await carte("""<div class="filet-carte"></div>
          <h1>Jeunesse, vieillesse, abstention&nbsp;: comment l'abstention différenciée pèse-t-elle sur le résultat des élections passées et à venir&nbsp;?</h1>
          <p class="grand">Découvrez les effets possibles de la mobilisation de chaque génération.</p>""")
        await pause(0.6)
        if not COURT:
            await page.screenshot(path=str(SORTIE / "couverture_linkedin.png"))

        await cdp.send("Page.stopScreencast")
        await pause(0.3)
        await contexte.close()
        await navigateur.close()

    # Liste d'images pour ffmpeg : chaque image reste affichée jusqu'à la suivante.
    liste = brut / "images.txt"
    lignes = []
    for (chemin, debut), (_, fin) in zip(images, images[1:] + [(None, images[-1][1] + 1.0)]):
        lignes += [f"file '{chemin.name}'", f"duration {max(fin - debut, 0.001):.4f}"]
    lignes.append(f"file '{images[-1][0].name}'")
    liste.write_text("\n".join(lignes), encoding="utf-8")

    # Conversion en MP4 (H.264, 30 images par seconde), le format recommandé par LinkedIn
    mp4 = SORTIE / ("simulateur_linkedin_30s.mp4" if COURT else "simulateur_linkedin.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste),
                    "-vf", f"fps=30,scale={LARGEUR * ECHELLE}:{HAUTEUR * ECHELLE}:flags=lanczos,format=yuv420p",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-movflags", "+faststart", "-an", str(mp4)],
                   check=True)
    shutil.rmtree(brut, ignore_errors=True)
    print(f"Vidéo : {mp4}  ({mp4.stat().st_size / 1e6:.1f} Mo)")


if __name__ == "__main__":
    asyncio.run(main())
