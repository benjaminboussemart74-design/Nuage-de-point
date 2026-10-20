"""
Enregistre une vidéo de démonstration du simulateur pour LinkedIn (format vertical 4:5, 1080 × 1350).

Le script ouvre la page dans un navigateur sans écran, joue un parcours de visiteur
(scénarios, curseurs, courbes) avec un curseur visible et des légendes à l'écran.
Chaque image affichée est capturée par le protocole de débogage de Chromium (« screencast »)
avec son horodatage, puis ffmpeg assemble ces images en MP4 lisible par LinkedIn.

Utilisation :
    python scripts/video_linkedin.py
Sortie : videos/simulateur_linkedin.mp4 et videos/couverture_linkedin.png
"""

import asyncio
import base64
import shutil
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

RACINE = Path(__file__).resolve().parent.parent
PAGE = (RACINE / "cohortes-presidentielle" / "index.html").as_uri()
SORTIE = RACINE / "videos"
CHROMIUM = "/opt/pw-browsers/chromium"

# Format vertical 4:5 : la page est affichée en 540 × 675 points, rendue deux fois plus fine.
LARGEUR, HAUTEUR, ECHELLE = 540, 675, 2

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
#video-carte h1 { font-size: 2.3rem; }
#video-carte p { font-size: 17px; color: var(--text-secondary); margin: 0; line-height: 1.5; }
#video-carte .petit { font-size: 12px; color: var(--text-muted); }
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

        async def legende(texte):
            await page.evaluate("t => { const l = document.getElementById('video-legende'); l.textContent = t; l.hidden = !t; }", texte)

        async def carte(html):
            await page.evaluate("h => { const c = document.getElementById('video-carte'); c.innerHTML = h; c.hidden = !h; }", html)

        async def defiler(selecteur, marge=180):
            await page.evaluate("""([s, m]) => {
              const e = document.querySelector(s);
              window.scrollTo({ top: e.getBoundingClientRect().top + window.scrollY - m, behavior: 'smooth' });
            }""", [selecteur, marge])
            await pause(1.0)

        async def viser(selecteur):
            boite = await page.locator(selecteur).first.bounding_box()
            x, y = boite["x"] + boite["width"] / 2, boite["y"] + boite["height"] / 2
            await page.evaluate("([x, y]) => { const c = document.getElementById('video-curseur'); c.style.left = x + 'px'; c.style.top = y + 'px'; }", [x, y])
            await pause(0.7)
            return x, y

        async def cliquer(selecteur):
            await viser(selecteur)
            await page.evaluate("() => document.getElementById('video-curseur').classList.add('clic')")
            await page.locator(selecteur).first.click()
            await pause(0.15)
            await page.evaluate("() => document.getElementById('video-curseur').classList.remove('clic')")

        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                                "maxWidth": LARGEUR * ECHELLE, "maxHeight": HAUTEUR * ECHELLE})

        # 1. Carte de titre
        await carte("""<div class="filet-carte"></div>
          <h1>Et si les jeunes votaient autant que leurs aînés&nbsp;?</h1>
          <p>Un simulateur de la présidentielle 2027 : changez la participation et le vote de chaque génération, et regardez le résultat bouger.</p>""")
        await pause(3.2)
        await carte("")
        await pause(0.5)

        # 2. Point de départ : le sondage
        await defiler("#sim-label")
        await legende("Point de départ : le sondage Ipsos-CEVIPOF de septembre 2026, 13 060 inscrits")
        await pause(3.0)

        # 3. Scénarios prêts à l'emploi
        await legende("1. Choisissez un scénario")
        await defiler("#scenarios")
        await cliquer('[data-scenario="jeunes-participent"]')
        await legende("Les moins de 35 ans votent autant que les 60-69 ans…")
        await pause(0.6)
        await defiler("#sim-liste")
        await legende("Les points pleins glissent : Mélenchon gagne un point")
        await pause(3.2)

        await legende("1. Choisissez un scénario")
        await defiler("#scenarios")
        await cliquer('[data-scenario="aines-comme-jeunes"]')
        await legende("Les 60 ans et plus votent comme les 25-34 ans…")
        await pause(0.6)
        await defiler("#sim-titre")
        await legende("… et le second tour change d'affiche")
        await pause(3.4)

        # 4. Réglage à la main d'une tranche d'âge
        await legende("2. Ou réglez chaque âge vous-même")
        await cliquer('[data-scenario="reel"]')
        await defiler("#sim-ages")
        x, y = await viser("#sim-p-0")
        for valeur in range(68, 101, 2):
            await page.evaluate("v => { const i = document.getElementById('sim-p-0'); i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); }", valeur)
            await page.evaluate("v => { const c = document.getElementById('video-curseur'); const r = document.getElementById('sim-p-0').getBoundingClientRect(); c.style.left = (r.left + 7 + (r.width - 14) * v / 100) + 'px'; }", valeur)
            await pause(0.07)
        await legende("Tous les 18-24 ans votent : 100 %")
        await pause(1.4)
        await defiler("#sim-liste")
        await pause(2.6)

        # 5. Courbes du vote par âge
        await legende("3. Comparez les électorats par âge")
        await defiler("#courbes-cles")
        await cliquer('[data-cle="melenchon"]')
        await legende("Mélenchon : 41 % chez les 18-24 ans, 4 % chez les 70 ans et plus")
        await pause(3.0)
        await cliquer('[data-cle="philippe"]')
        await legende("Philippe : l'inverse, son électorat vieillit")
        await pause(3.0)

        # 6. Carte de fin
        await legende("")
        await carte("""<div class="filet-carte"></div>
          <h1>À vous de jouer</h1>
          <p>Choisissez un scénario, réglez chaque génération, et voyez qui se qualifierait au second tour.</p>
          <p class="petit">Sources : Ipsos bva - CEVIPOF, Enquête électorale française 2026 ; Ipsos, Sociologie des électorats 2022 et 2024 ; INSEE ; ministère de l'Intérieur. Simulation à titre indicatif.</p>""")
        await pause(3.5)

        # Image de couverture, prise sur la carte de titre
        await carte("""<div class="filet-carte"></div>
          <h1>Et si les jeunes votaient autant que leurs aînés&nbsp;?</h1>
          <p>Un simulateur de la présidentielle 2027 : changez la participation et le vote de chaque génération, et regardez le résultat bouger.</p>""")
        await pause(0.6)
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
    mp4 = SORTIE / "simulateur_linkedin.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste),
                    "-vf", f"fps=30,scale={LARGEUR * ECHELLE}:{HAUTEUR * ECHELLE}:flags=lanczos,format=yuv420p",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-movflags", "+faststart", "-an", str(mp4)],
                   check=True)
    shutil.rmtree(brut, ignore_errors=True)
    print(f"Vidéo : {mp4}  ({mp4.stat().st_size / 1e6:.1f} Mo)")


if __name__ == "__main__":
    asyncio.run(main())
