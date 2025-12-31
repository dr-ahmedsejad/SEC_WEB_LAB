import urllib.parse
# 1. Le Contexte : On a un serveur et un utilisateur à chercher
base_url = "http://localhost:5000/search"
email = "ahmed.sejad@esp.mr"
# 2. Encodage de la donnée (La valeur du paramètre)
# IMPORTANT : On n'encode QUE la donnée, pas l'URL entière !
email_encoded = urllib.parse.quote(email)
# 3. Construction de l'URL finale
# On assemble : [Site] + [?] + [Paramètre=] + [Donnée Encodée]
full_url = f"{base_url}?query={email_encoded}"
print("--- Simulation de la requête ---")
print(f"Donnée brute : {email}")
print(f"Donnée sûre  : {email_encoded}")
print("-" * 10)
print(f"URL FINALE   : {full_url}")
# Résultat affiché :
# URL FINALE : http://localhost:5000/search?query=ahmed.sejad%40esp.mr

