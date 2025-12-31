from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# --- 1. GÉNÉRATION DES CLÉS (Comme vu précédemment) ---
# On crée la paire de clés (Privée + Publique)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
public_key = private_key.public_key()

# --- 2. LE MESSAGE ---
# Attention : RSA ne peut chiffrer que des petites données (plus petites que la clé)
message_secret = b"Ceci est un petit secret !"
print(f"Message original : {message_secret.decode()}")

# --- 3. CHIFFREMENT (Avec la Clé Publique) ---
# On utilise le padding OAEP (Obligatoire pour sécuriser RSA aujourd'hui)
ciphertext = public_key.encrypt(
    message_secret,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print(f"\nMessage chiffré (Hex) :\n{ciphertext.hex()}")

# --- 4. DÉCHIFFREMENT (Avec la Clé Privée) ---
# Seule la clé privée associée peut inverser le processus
try:
    decrypted_message = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    print(f"\nMessage déchiffré : {decrypted_message.decode()}")

except Exception as e:
    print("Échec du déchiffrement (Clé incorrecte ou message altéré)")