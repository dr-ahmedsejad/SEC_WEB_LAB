import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Génération d'une clé AES 256 bits et d'un vecteur d'initialisation (IV)
key = os.urandom(32)
iv = os.urandom(12) # Requis pour le mode GCM

# Chiffrement
cipher = Cipher(algorithms.AES(key), modes.GCM(iv))

encryptor = cipher.encryptor()

ciphertext = encryptor.update(b"Donnees Confidentielles") + encryptor.finalize()

print(f"Message chiffré (Hex): {ciphertext.hex()}")


