import base64
# Nom de votre fichier image
image_path = "MR.png"
try:
    # 1. Ouvrir l'image en mode "lecture binaire" ('rb')
    with open(image_path, "rb") as image_file:
        # 2. Lire le contenu du fichier
        binary_data = image_file.read()
        # 3. Encoder les données binaires en Base64 (cela produit des bytes)
        base64_encoded_data = base64.b64encode(binary_data)
        # 4. Convertir les bytes en chaîne de caractères (string) pour l'affichage/JSON
        base64_string = base64_encoded_data.decode('utf-8')
        print("Encodage réussi !")
        print("-" * 30)
        # On affiche juste les 50 premiers caractères car la chaîne est très longue
        print(f"Début du code Base64 : {base64_string[:50]}...")
        print(base64_string)
except FileNotFoundError:
    print(f"Erreur : Le fichier '{image_path}' est introuvable.")

