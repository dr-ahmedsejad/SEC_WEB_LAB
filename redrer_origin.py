from urllib.parse import urlparse

from flask import request, session, app, redirect


@app.route('/transfert', methods=['POST'])
def transfert():
    if 'user_id' not in session: return redirect('/login')

    # --- DÉBUT PROTECTION REFERER ---

    # 1. On récupère les en-têtes (Referer ou Origin)
    referer = request.headers.get('Referer')
    origin = request.headers.get('Origin')

    # 2. On définit notre domaine de confiance
    domaine_legitime = "elbarak-shop.online"  #

    # 3. Vérification stricte
    # Si le referer existe, est-ce qu'il contient notre domaine ?
    if referer and domaine_legitime not in referer:
        return "⛔ ERREUR : Requête venant d'une source non autorisée (Referer suspect).", 403

    # Idem pour Origin (souvent envoyé par les navigateurs modernes sur les POST)
    if origin and domaine_legitime not in origin:
        return "⛔ ERREUR : Requête venant d'une source non autorisée (Origin suspect).", 403

    # --- FIN PROTECTION REFERER ---

    # ... Suite du code de transfert ...