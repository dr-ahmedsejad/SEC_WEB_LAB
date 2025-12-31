import sqlite3
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes, hmac, padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
import datetime


# ==============================================================================
# 0. CONFIGURATION & OUTILS (Infrastructure PKI)
# ==============================================================================

def generate_identity(name):
    """Génère une paire de clés RSA et un certificat X.509 (Simulation Identité)"""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        key.public_key()
    ).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).sign(key, hashes.SHA256())
    return key, cert


def setup_database():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect('passkeeper.db')
    cursor = conn.cursor()
    # On stocke tout en BLOB (Binaire) pour éviter les problèmes d'encodage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT UNIQUE,
            enc_aes_key BLOB,    -- La clé AES chiffrée par RSA (Pour le destinataire)
            iv BLOB,             -- Vecteur d'initialisation AES
            ciphertext BLOB,     -- Le mot de passe chiffré par AES
            signature BLOB,      -- La signature de l'auteur
            hmac BLOB,           -- Le code d'intégrité
            author_cert BLOB     -- Le certificat de l'auteur (pour vérifier la signature)
        )
    ''')
    conn.commit()
    return conn


# ==============================================================================
# CLASSE PRINCIPALE : LE COFFRE-FORT (Respect du Flux 1-6)
# ==============================================================================
class SecureVault:
    def __init__(self):
        self.conn = setup_database()

    # --------------------------------------------------------------------------
    # ÉCRITURE (Alice) : FLUX 1 -> 2 -> 3 -> 4 -> 5
    # --------------------------------------------------------------------------
    def store_password(self, label, clear_password, sender_priv_key, sender_cert, recipient_cert):
        print(f"\n🔐 [Vault] Traitement de sécurisation pour : '{label}'")

        # FLUX 1 : Alice fournit le mot de passe clair ("clear_password")
        data_bytes = clear_password.encode('utf-8')

        # FLUX 2 : Moteur Symétrique (AES) -> Chiffrement de la donnée
        # On génère une clé AES unique pour cette entrée
        aes_key = os.urandom(32)
        iv = os.urandom(16)

        # Chiffrement AES-CBC avec Padding
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data_bytes) + padder.finalize()
        ciphertext_blob = encryptor.update(padded_data) + encryptor.finalize()
        print("   ✅ 2. AES : Donnée chiffrée (Symétrique).")

        # FLUX 3 : Moteur Asymétrique (RSA) -> Protection de la clé AES
        # On chiffre la clé AES avec la Clé Publique du DESTINATAIRE (Bob)
        recipient_pub_key = recipient_cert.public_key()
        encrypted_aes_key_blob = recipient_pub_key.encrypt(
            aes_key,
            asym_padding.OAEP(mgf=asym_padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        print("   ✅ 3. RSA : Clé AES encapsulée pour le destinataire (Hybride).")

        # FLUX 4 : Moteur Signature -> Alice signe le chiffré
        # Elle utilise SA Clé Privée. Cela garantit la Non-Répudiation.
        signature_blob = sender_priv_key.sign(
            ciphertext_blob,
            asym_padding.PSS(mgf=asym_padding.MGF1(hashes.SHA256()), salt_length=asym_padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        print("   ✅ 4. Signature : Contenu signé par l'auteur.")

        # EXTRA : Calcul HMAC (Pour l'intégrité technique de la DB)
        h = hmac.HMAC(aes_key, hashes.SHA256())
        h.update(ciphertext_blob)
        hmac_blob = h.finalize()

        # FLUX 5 : Stockage -> Insertion dans SQLite
        # On doit sérialiser le certificat de l'auteur pour le stocker
        author_cert_pem = sender_cert.public_bytes(serialization.Encoding.PEM)

        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO secrets (label, enc_aes_key, iv, ciphertext, signature, hmac, author_cert)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (label, encrypted_aes_key_blob, iv, ciphertext_blob, signature_blob, hmac_blob, author_cert_pem))
            self.conn.commit()
            print("   ✅ 5. Storage : Données persistées dans 'passkeeper.db'.")
        except sqlite3.IntegrityError:
            print("   ❌ Erreur : Ce label existe déjà dans la base.")

    # --------------------------------------------------------------------------
    # LECTURE (Bob) : FLUX 6 (Decrypt RSA -> HMAC -> Verify Sig -> Decrypt AES)
    # --------------------------------------------------------------------------
    def retrieve_password(self, label, user_priv_key):
        print(f"\n🔓 [Vault] Tentative de récupération : '{label}'")

        cursor = self.conn.cursor()
        cursor.execute('SELECT enc_aes_key, iv, ciphertext, signature, hmac, author_cert FROM secrets WHERE label = ?',
                       (label,))
        row = cursor.fetchone()

        if not row:
            print("   ❌ Entrée introuvable dans la BD.")
            return

        enc_aes_key, iv, ciphertext, signature, stored_hmac, author_cert_pem = row

        try:
            # ÉTAPE A : Déchiffrement RSA de la clé AES (Hybride)
            # Bob utilise SA clé privée. Si ça échoue, c'est que le secret n'était pas pour lui.
            aes_key = user_priv_key.decrypt(
                enc_aes_key,
                asym_padding.OAEP(mgf=asym_padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
            )
            print("   ✅ 6a. RSA : Clé AES récupérée.")

            # ÉTAPE B : Vérification HMAC (Intégrité)
            h = hmac.HMAC(aes_key, hashes.SHA256())
            h.update(ciphertext)
            h.verify(stored_hmac)
            print("   ✅ 6b. HMAC : Intégrité base de données validée.")

            # ÉTAPE C : Vérification Signature (Authentification Auteur)
            # On recharge le certificat stocké de l'auteur
            author_cert = x509.load_pem_x509_certificate(author_cert_pem, default_backend())
            author_pub_key = author_cert.public_key()

            author_pub_key.verify(
                signature,
                ciphertext,
                asym_padding.PSS(mgf=asym_padding.MGF1(hashes.SHA256()), salt_length=asym_padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            # Récupérer le nom de l'auteur pour l'affichage
            author_name = author_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            print(f"   ✅ 6c. Signature : Validée. Auteur certifié = {author_name}")

            # ÉTAPE D : Déchiffrement AES (Symétrique)
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_pass = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = sym_padding.PKCS7(128).unpadder()
            clear_password = unpadder.update(padded_pass) + unpadder.finalize()

            print(f"   🤫 SECRET DÉVOILÉ : {clear_password.decode('utf-8')}")

        except Exception as e:
            print(f"   ⛔ ERREUR DE SÉCURITÉ : Accès refusé ou données corrompues. ({e})")


# ==============================================================================
# EXECUTION DU SCÉNARIO
# ==============================================================================

# 1. Nettoyage de la DB précédente pour le test
if os.path.exists("passkeeper.db"):
    os.remove("passkeeper.db")

# 2. Création des acteurs
alice_priv, alice_cert = generate_identity(u"Alice (Admin)")
bob_priv, bob_cert = generate_identity(u"Bob (Tech)")
eve_priv, eve_cert = generate_identity(u"Eve (Hacker)")

# 3. Initialisation du coffre
vault = SecureVault()

# --- SCÉNARIO : ALICE DÉPOSE UN SECRET POUR BOB ---
# Elle chiffre pour Bob (bob_cert) et signe avec sa clé (alice_priv)
vault.store_password(
    label="Serveur_Prod_Root",
    clear_password="Azerty123!",
    sender_priv_key=alice_priv,
    sender_cert=alice_cert,
    recipient_cert=bob_cert
)

# --- SCÉNARIO : BOB RÉCUPÈRE LE SECRET ---
# Il utilise sa clé privée pour lire
vault.retrieve_password("Serveur_Prod_Root", bob_priv)

# --- SCÉNARIO : EVE ESSAIE DE LIRE ---
# Elle utilise sa clé privée de hacker
print("\n--- Tentative d'intrusion par Eve ---")
vault.retrieve_password("Serveur_Prod_Root", eve_priv)
# Résultat attendu : Erreur RSA (car la clé AES n'a pas été chiffrée pour Eve)