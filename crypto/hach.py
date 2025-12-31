import hashlib
# SHA-256 est le standard actuel
print(hashlib.sha256(b"Bonjour Ahmed").hexdigest())
# Résultat : 8982a... (unique)

import hashlib
message = "MonMotDePasse".encode()
# Création du hash SHA-256
hash_object = hashlib.sha256(message)
hex_dig = hash_object.hexdigest()
print(f"Empreinte SHA-256 : {hex_dig}")
# Si on change une lettre, tout le hash change (Effet avalanche)

