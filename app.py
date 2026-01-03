from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
# app.secret_key = 'mauritanie_ctf_secret_key'
# app.config['SESSION_COOKIE_HTTPONLY'] = False
# 🔑 CLÉ FIXE : Indispensable pour ne pas perdre la session au redémarrage
app.secret_key = 'mauritanie_ctf_secret_key'

# ⚙️ CONFIGURATION DES COOKIES POUR PERMETTRE L'ATTAQUE
# On reste en 'Lax' (comportement par défaut).
# Cela permet l'attaque via /promo_ramadan (Same-Site) sans soucis.
# Pour une attaque externe, Firefox est recommandé.
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['SESSION_COOKIE_SECURE'] = False  # False car on est en HTTP (localhost)
app.config['SESSION_COOKIE_HTTPONLY'] = False # False pour faciliter le vol XSS si besoin

HTTPONLY = False


def get_db_connection():
    conn = sqlite3.connect('elbaraka.db')
    conn.row_factory = sqlite3.Row
    return conn


import secrets
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()


    query = f"SELECT * FROM utilisateurs WHERE username = '{username}' AND password = '{password}'"


    try:
        user = conn.execute(query).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['solde_mru'] = user['solde_mru']
            session['est_admin'] = user['est_admin']
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


@app.route('/transfert', methods=['POST'])
def transfert():
    if 'user_id' not in session: return redirect('/login')
    destinataire = request.form['destinataire']
    montant = int(request.form['montant'])
    sender_id = session['user_id']

    conn = get_db_connection()

    # 1. Vérifier si le destinataire existe
    user_dest = conn.execute("SELECT id, solde_mru FROM utilisateurs WHERE username = ?", (destinataire,)).fetchone()

    # 2. Vérifier le solde de l'envoyeur
    user_sender = conn.execute("SELECT solde_mru FROM utilisateurs WHERE id = ?", (sender_id,)).fetchone()

    if user_dest and user_sender and user_sender['solde_mru'] >= montant and montant > 0:
        # On effectue le transfert
        # Débiter l'envoyeur
        conn.execute("UPDATE utilisateurs SET solde_mru = solde_mru - ? WHERE id = ?", (montant, sender_id))
        # Créditer le destinataire
        conn.execute("UPDATE utilisateurs SET solde_mru = solde_mru + ? WHERE id = ?", (montant, user_dest['id']))

        conn.commit()
        flash(f"✅ Transfert réussi ! Vous avez envoyé {montant} MRU à {destinataire}.", "success")
    else:
        flash("❌ Échec du transfert : Solde insuffisant ou destinataire introuvable.", "danger")

    conn.close()
    return redirect('/')


@app.route('/acheter/<int:produit_id>', methods=['POST'])
def acheter_produit(produit_id):
    if 'user_id' not in session: return redirect('/login')
    qty = request.form['qty']
    print(qty)
    user_id = session['user_id']
    conn = get_db_connection()

    qty = int(request.form['qty'])
    # Interdiction formelle des nombres négatifs ou nuls
    if qty <= 0:
        flash("Erreur : Vous devez commander au moins 1 article.")
        return redirect(url_for('index'))

    try:
        # 1. Récupérer les infos du produit et de l'utilisateur
        produit = conn.execute("SELECT * FROM produits WHERE id = ?", (produit_id,)).fetchone()
        user = conn.execute("SELECT * FROM utilisateurs WHERE id = ?", (user_id,)).fetchone()
        prix_achat = float(produit['prix']) * float(qty)
        # 2. Vérifications de base
        if not produit:
            flash("Produit introuvable.", "danger")
            return redirect('/')

        if produit['quantite'] <= 0:
            flash("Stock épuisé !", "warning")
            return redirect('/')

        if user['solde_mru'] < prix_achat:
            flash("Solde insuffisant pour cet achat.", "danger")
            return redirect('/')


        # 3. TRANSACTION D'ACHAT
        # A. Débiter l'utilisateur
        conn.execute("UPDATE utilisateurs SET solde_mru = solde_mru - ? WHERE id = ?", (prix_achat, user_id))

        # B. Baisser le stock
        conn.execute("UPDATE produits SET quantite =quantite - ? WHERE id = ?", (qty,produit_id,))

        # C. Créer la commande (Facture)
        cur = conn.execute("""
            INSERT INTO commandes (utilisateur_id, produit_id, montant, adresse_livraison)
            VALUES (?, ?, ?, ?)
        """, (user_id, produit_id, prix_achat, user['adresse']))

        # On récupère l'ID de la commande qu'on vient de créer (ex: 3)
        id_nouvelle_facture = cur.lastrowid

        conn.commit()

        flash("✅ Achat effectué avec succès !", "success")

        # 4. REDIRECTION VERS LA FACTURE (Le piège pour l'IDOR)
        # On envoie l'utilisateur directement sur SA facture
        return redirect(f'/commande/{id_nouvelle_facture}')

    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de l'achat : {e}", "danger")
        return redirect('/')
    finally:
        conn.close()


# @app.route('/commande/<int:id_commande>')
# def voir_commande(id_commande):
#     if 'user_id' not in session:
#         return redirect('/login')
#
#     conn = get_db_connection()
#
#     # ❌ CODE VULNÉRABLE A01 : IDOR
#     # On fait une jointure pour récupérer le nom du produit associé à l'ID stocké dans la commande
#     # Mais on ne vérifie TOUJOURS PAS à qui appartient la commande !
#     query = """
#         SELECT c.*, p.nom as nom_produit, p.description
#         FROM commandes c
#         JOIN produits p ON c.produit_id = p.id
#         WHERE c.id = ?
#     """
#     commande = conn.execute(query, (id_commande,)).fetchone()
#
#     conn.close()
#
#     if commande:
#         return render_template('commande.html', c=commande)
#     else:
#         return "❌ Commande introuvable."

# @app.route('/commande/<int:id_commande>')
# def voir_commande(id_commande):
#     if 'user_id' not in session: return redirect('/login')
#     conn = get_db_connection()
#     query = """
#         SELECT c.*, p.nom as nom_produit, p.description
#         FROM commandes c
#         JOIN produits p ON c.produit_id = p.id
#         WHERE c.id = ?
#     """
#     commande = conn.execute(query, (id_commande,)).fetchone()
#     conn.close()
#
#     if commande:
#         return render_template('commandes.html', commande=commande)
#     else:
#         return "❌ Commande introuvable."

@app.route('/commande/<int:id_commande>')
def voir_commande(id_commande):
    if 'user_id' not in session: return redirect('/login')

    conn = get_db_connection()

    query = """
        SELECT c.*, 
               p.nom as nom_produit, 
               p.description,
               u.username as nom_client,
               u.telephone as tel_client
        FROM commandes c
        JOIN produits p ON c.produit_id = p.id
        JOIN utilisateurs u ON c.utilisateur_id = u.id
        WHERE c.id = ?
    """

    commande = conn.execute(query, (id_commande,)).fetchone()
    conn.close()

    if commande:
        # On passe toujours une liste pour garder la compatibilité avec le template
        return render_template('commande.html', commande=commande, titre=f"Détail Commande #{id_commande}")
    else:
        flash("Commande introuvable.", "danger")
        return redirect('/')


@app.route('/mes-commandes')
def mes_commandes():
    if 'user_id' not in session: return redirect('/login')
    user_id = session['user_id']
    conn = get_db_connection()

    query = """
        SELECT c.*, p.nom as nom_produit, p.description 
        FROM commandes c
        JOIN produits p ON c.produit_id = p.id 
        JOIN utilisateurs u ON c.utilisateur_id = u.id
        WHERE c.utilisateur_id = ?
    """
    commandes = conn.execute(query,(user_id,)).fetchall()
    conn.close()

    if commandes:
        return render_template('commandes.html', commandes=commandes)
    else:
        flash("Commande introuvable.", "danger")
        return redirect('/')



# ============================================
# CRUD ADMIN - GESTION DES UTILISATEURS
# ============================================

@app.route('/admin/users')
def admin_users():
    """Afficher la liste de tous les utilisateurs"""
    if 'user_id' not in session: return redirect('/login')
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM utilisateurs ORDER BY id ASC").fetchall()
    conn.close()

    return render_template('admin_users.html', users=users)


@app.route('/admin/users/add', methods=['POST'])
def admin_add_user():
    """Ajouter un nouvel utilisateur"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    telephone = request.form.get('telephone', '').strip()
    adresse = request.form.get('adresse', '').strip()
    solde_mru = request.form.get('solde_mru', '0.00')
    est_admin = 1 if request.form.get('est_admin') else 0

    # Validation
    if not username or not password:
        flash("Le nom d'utilisateur et le mot de passe sont obligatoires.", "danger")
        return redirect('/admin/users')

    if len(password) < 6:
        flash("Le mot de passe doit contenir au moins 6 caractères.", "danger")
        return redirect('/admin/users')

    conn = get_db_connection()

    # Vérifier si le username existe déjà
    existing = conn.execute("SELECT id FROM utilisateurs WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        flash(f"L'utilisateur '{username}' existe déjà.", "danger")
        return redirect('/admin/users')

    try:
        # Insérer le nouvel utilisateur
        conn.execute("""
            INSERT INTO utilisateurs (username, password, telephone, adresse, solde_mru, est_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password, telephone, adresse, float(solde_mru), est_admin))




        conn.commit()
        flash(f"✅ Utilisateur '{username}' créé avec succès !", "success")
    except Exception as e:
        flash(f"Erreur lors de la création : {e}", "danger")
    finally:
        conn.close()

    return redirect('/admin/users')


@app.route('/admin/users/edit', methods=['POST'])
def admin_edit_user():
    """Modifier un utilisateur existant"""
    user_id = request.form.get('user_id')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    telephone = request.form.get('telephone', '').strip()
    adresse = request.form.get('adresse', '').strip()
    solde_mru = request.form.get('solde_mru', '0.00')
    est_admin = 1 if request.form.get('est_admin') else 0

    if not user_id or not username:
        flash("Données invalides.", "danger")
        return redirect('/admin/users')

    conn = get_db_connection()

    # Vérifier si le username existe déjà pour un autre utilisateur
    existing = conn.execute(
        "SELECT id FROM utilisateurs WHERE username = ? AND id != ?",
        (username, user_id)
    ).fetchone()

    if existing:
        conn.close()
        flash(f"Le nom d'utilisateur '{username}' est déjà utilisé par un autre compte.", "danger")
        return redirect('/admin/users')

    try:
        # Si un mot de passe est fourni, le mettre à jour aussi
        if password and len(password) >= 6:
            conn.execute("""
                UPDATE utilisateurs 
                SET username = ?, password = ?, telephone = ?, adresse = ?, solde_mru = ?, est_admin = ?
                WHERE id = ?
            """, (username, password, telephone, adresse, float(solde_mru), est_admin, user_id))
        else:
            # Sinon, ne pas toucher au mot de passe
            conn.execute("""
                UPDATE utilisateurs 
                SET username = ?, telephone = ?, adresse = ?, solde_mru = ?, est_admin = ?
                WHERE id = ?
            """, (username, telephone, adresse, float(solde_mru), est_admin, user_id))

        conn.commit()
        flash(f"✅ Utilisateur '{username}' modifié avec succès !", "success")
    except Exception as e:
        flash(f"Erreur lors de la modification : {e}", "danger")
    finally:
        conn.close()

    return redirect('/admin/users')


@app.route('/admin/users/delete', methods=['POST'])
def admin_delete_user():
    user_id = request.form.get('user_id')
    if not user_id:
        flash("ID utilisateur manquant.", "danger")
        return redirect('/admin/users')

    # Empêcher la suppression de son propre compte
    if int(user_id) == session.get('user_id'):
        flash("⚠️ Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect('/admin/users')

    conn = get_db_connection()

    try:
        # Récupérer le nom avant suppression
        user = conn.execute("SELECT username FROM utilisateurs WHERE id = ?", (user_id,)).fetchone()

        if user and session['est_admin']==True:
            # Supprimer l'utilisateur
            conn.execute("DELETE FROM utilisateurs WHERE id = ?", (user_id,))
            conn.commit()
            flash(f"✅ Utilisateur '{user['username']}' supprimé avec succès.", "success")
        else:
            flash("Utilisateur introuvable.", "danger")
    except Exception as e:
        flash(f"Erreur lors de la suppression : {e}", "danger")
    finally:
        conn.close()

    return redirect('/admin/users')

@app.route('/promo_ramadan')
def promo():
    return render_template('csrf_exploit.html')

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=5555)






