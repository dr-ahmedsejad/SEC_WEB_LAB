import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# --- 1. PRÉPARATION ---
# Clé AES 256 bits et IV de 12 octets
key = os.urandom(32)
iv = os.urandom(12)

print("--- CHIFFREMENT ---")
# --- 2. CHIFFREMENT ---
# On initialise le mode GCM avec l'IV
cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
encryptor = cipher.encryptor()

# Le message à protéger
message_secret = b"Donnees Confidentielles"

# On chiffre et on finalise
ciphertext = encryptor.update(message_secret) + encryptor.finalize()

# IMPORTANT : On récupère le "Tag" (la signature d'intégrité) généré par GCM
tag = encryptor.tag

print(f"Message chiffré (Hex): {ciphertext.hex()}")
print(f"Tag d'intégrité (Hex): {tag.hex()}")

print("\n--- DÉCHIFFREMENT ---")
# --- 3. DÉCHIFFREMENT ---
# Pour déchiffrer, il faut fournir la clé, l'IV... ET le Tag !
# Si le Tag ne correspond pas, le déchiffrement échouera (preuve de modification).
cipher_dec = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
decryptor = cipher_dec.decryptor()

# On récupère le message en clair
decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

print(f"Message déchiffré : {decrypted_data.decode('utf-8')}")