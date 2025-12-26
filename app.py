# from flask import Flask, render_template, request, redirect, session, flash, url_for
# import sqlite3
#
# app = Flask(__name__)
# app.secret_key = 'mauritanie_ctf_secret_key'
#
#
# def get_db_connection():
#     conn = sqlite3.connect('elbaraka.db')
#     conn.row_factory = sqlite3.Row
#     return conn
#
#
# # Route Accueil
# @app.route('/')
# def index():
#     if 'user_id' not in session:
#         return redirect('/login')
#
#     conn = get_db_connection()
#
#     # Mise à jour du solde affiché
#     user = conn.execute("SELECT solde_mru FROM utilisateurs WHERE id = ?", (session['user_id'],)).fetchone()
#     if user:
#         session['solde_mru'] = user['solde_mru']
#
#     # Par défaut, on affiche quelques produits
#     produits = conn.execute("SELECT * FROM produits LIMIT 10").fetchall()
#     conn.close()
#
#     return render_template('index.html', produits=produits, search_term='')
#
#
# # Route Login (Avec la faille SQL)
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'GET':
#         return render_template('login.html')
#
#     username = request.form['username']
#     password = request.form['password']
#
#     conn = get_db_connection()
#
#     # ❌ VULNÉRABILITÉ A05 : Concaténation directe
#     # Payload: admin_baraka' --
#     query = f"SELECT * FROM utilisateurs WHERE username = '{username}' AND password = '{password}'"
#
#     try:
#         user = conn.execute(query).fetchone()
#         conn.close()
#
#         if user:
#             session['user_id'] = user['id']
#             session['username'] = user['username']
#             session['solde_mru'] = user['solde_mru']
#             flash(f"Marhba {user['username']} !", "success")
#             return redirect('/')
#         else:
#             flash("Identifiants incorrects.", "danger")
#             return redirect('/login')
#     except Exception as e:
#         flash(f"Erreur SQL : {e}", "danger")  # Affiche l'erreur pour aider le hacker
#         return redirect('/login')
#
#
# # Route Recherche (Avec la faille UNION SQL)
# @app.route('/recherche')
# def recherche():
#     if 'user_id' not in session: return redirect('/login')
#
#     q = request.args.get('q', '')
#     conn = get_db_connection()
#
#     # ❌ VULNÉRABILITÉ A05 : UNION SELECT possible ici
#     # La requête attend 5 colonnes : id, nom, description, prix, quantite
#     sql = f"SELECT id, nom, description, prix, quantite FROM produits WHERE nom LIKE '%{q}%'"
#
#     try:
#         produits = conn.execute(sql).fetchall()
#     except Exception as e:
#         produits = []
#         flash(f"Erreur SQL: {e}", "danger")
#
#     conn.close()
#     return render_template('index.html', produits=produits, search_term=q)
#
#
# # Route Recharge (Fonctionnelle, pas vulnérable, sert à valider le vol)
# @app.route('/recharger', methods=['POST'])
# def recharger():
#     if 'user_id' not in session: return redirect('/login')
#
#     code = request.form['code_pin']
#     conn = get_db_connection()
#
#     # Vérification propre
#     carte = conn.execute("SELECT * FROM cartes_recharge WHERE code_pin = ? AND statut = 'VALIDE'", (code,)).fetchone()
#
#     if carte:
#         montant = carte['montant']
#         # 1. Invalider la carte
#         conn.execute("UPDATE cartes_recharge SET statut = 'UTILISE' WHERE id = ?", (carte['id'],))
#         # 2. Donner l'argent
#         conn.execute("UPDATE utilisateurs SET solde_mru = solde_mru + ? WHERE id = ?", (montant, session['user_id']))
#         conn.commit()
#         flash(f"Félicitations ! Votre compte a été crédité de {montant} MRU.", "success")
#     else:
#         flash("Code invalide ou déjà utilisé.", "danger")
#
#     conn.close()
#     return redirect('/')
#
#
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect('/login')
#
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mauritanie_ctf_secret_key'


def get_db_connection():
    conn = sqlite3.connect('elbaraka.db')
    conn.row_factory = sqlite3.Row
    return conn


# Route Accueil
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()

    # Mise à jour du solde affiché
    user = conn.execute("SELECT solde_mru FROM utilisateurs WHERE id = ?", (session['user_id'],)).fetchone()
    if user:
        session['solde_mru'] = user['solde_mru']

    # Par défaut, on affiche quelques produits
    produits = conn.execute("SELECT * FROM produits LIMIT 10").fetchall()
    conn.close()

    return render_template('index.html', produits=produits, search_term='')


# Route Login (Avec la faille SQL)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()

    # ❌ VULNÉRABILITÉ A03 (SQL Injection) : Concaténation directe
    # Payload: admin_baraka' --
    query = f"SELECT * FROM utilisateurs WHERE username = '{username}' AND password = '{password}'"

    try:
        user = conn.execute(query).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['solde_mru'] = user['solde_mru']
            flash(f"Marhba {user['username']} !", "success")
            return redirect('/')
        else:
            flash("Identifiants incorrects.", "danger")
            return redirect('/login')
    except Exception as e:
        flash(f"Erreur SQL : {e}", "danger")  # Affiche l'erreur pour aider le hacker
        return redirect('/login')


# Route Recherche (Avec la faille UNION SQL)
@app.route('/recherche')
def recherche():
    if 'user_id' not in session: return redirect('/login')

    q = request.args.get('q', '')
    conn = get_db_connection()

    # ❌ VULNÉRABILITÉ A03 (SQL Injection - UNION) : UNION SELECT possible ici
    # La requête attend 5 colonnes : id, nom, description, prix, quantite
    sql = f"SELECT id, nom, description, prix, quantite FROM produits WHERE nom LIKE '%{q}%'"

    try:
        produits = conn.execute(sql).fetchall()
    except Exception as e:
        produits = []
        flash(f"Erreur SQL: {e}", "danger")

    conn.close()
    return render_template('index.html', produits=produits, search_term=q)


# Route Détails Produit (Avec affichage des commentaires)
@app.route('/produit/<int:produit_id>')
def produit_details(produit_id):
    if 'user_id' not in session: return redirect('/login')

    conn = get_db_connection()

    # Récupérer le produit
    produit = conn.execute("SELECT * FROM produits WHERE id = ?", (produit_id,)).fetchone()

    if not produit:
        flash("Produit introuvable.", "danger")
        conn.close()
        return redirect('/')

    # Récupérer les commentaires (avec jointure pour avoir le nom d'utilisateur)
    commentaires = conn.execute("""
        SELECT c.*, u.username
        FROM commentaires c
        JOIN utilisateurs u ON c.utilisateur_id = u.id
        WHERE c.produit_id = ?
        ORDER BY c.date_post DESC
    """, (produit_id,)).fetchall()

    conn.close()
    return render_template('produit_details.html', produit=produit, commentaires=commentaires)


# Route Ajouter Commentaire (Avec la faille XSS)
@app.route('/produit/<int:produit_id>/commenter', methods=['POST'])
def ajouter_commentaire(produit_id):
    if 'user_id' not in session: return redirect('/login')

    message = request.form.get('message', '')
    note = request.form.get('note', 5)

    # ❌ VULNÉRABILITÉ A03 (XSS - Cross-Site Scripting)
    # Le message n'est PAS échappé, permet l'injection de <script>
    # Payload: <script>alert('XSS!')</script>
    # Payload avancé: <script>fetch('/api/voler?cookie='+document.cookie)</script>

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO commentaires (produit_id, utilisateur_id, message, note, date_post)
            VALUES (?, ?, ?, ?, ?)
        """, (produit_id, session['user_id'], message, note, datetime.now()))

        conn.commit()
        flash("Commentaire ajouté avec succès !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'ajout du commentaire : {e}", "danger")

    conn.close()
    return redirect(f'/produit/{produit_id}')


# Route Recharge (Fonctionnelle, pas vulnérable, sert à valider le vol)
@app.route('/recharger', methods=['POST'])
def recharger():
    if 'user_id' not in session: return redirect('/login')

    code = request.form['code_pin']
    conn = get_db_connection()

    # Vérification propre (pas de vulnérabilité ici)
    carte = conn.execute("SELECT * FROM cartes_recharge WHERE code_pin = ? AND statut = 'VALIDE'", (code,)).fetchone()

    if carte:
        montant = carte['montant']
        # 1. Invalider la carte
        conn.execute("UPDATE cartes_recharge SET statut = 'UTILISE' WHERE id = ?", (carte['id'],))
        # 2. Donner l'argent
        conn.execute("UPDATE utilisateurs SET solde_mru = solde_mru + ? WHERE id = ?", (montant, session['user_id']))
        conn.commit()
        flash(f"Félicitations ! Votre compte a été crédité de {montant} MRU.", "success")
    else:
        flash("Code invalide ou déjà utilisé.", "danger")

    conn.close()
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True, port=5000)