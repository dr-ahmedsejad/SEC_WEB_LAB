import sqlite3


def init_db():
    # Connexion à la base de données (elle sera créée si elle n'existe pas)
    connection = sqlite3.connect('elbaraka.db')

    # On utilise un curseur pour exécuter les commandes SQL
    cursor = connection.cursor()

    # 1. NETTOYAGE : On supprime les tables existantes pour repartir à zéro
    # C'est utile si l'étudiant casse la base, il suffit de relancer ce script.
    cursor.executescript("""
        DROP TABLE IF EXISTS commentaires;
        DROP TABLE IF EXISTS commandes;
        DROP TABLE IF EXISTS cartes_recharge;
        DROP TABLE IF EXISTS produits;
        DROP TABLE IF EXISTS utilisateurs;
    """)

    # 2. CRÉATION DES TABLES (SCHEMA)
    cursor.executescript("""
        -- Table Utilisateurs
        CREATE TABLE utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            telephone TEXT,
            adresse TEXT,
            est_admin BOOLEAN DEFAULT 0,
            solde_mru DECIMAL(10, 2) DEFAULT 0.00
        );

        -- Table Produits
        CREATE TABLE produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT,
            prix DECIMAL(10, 2) NOT NULL,
            quantite INTEGER DEFAULT 10
        );
        
        CREATE TABLE commentaires (
        id INT AUTO_INCREMENT PRIMARY KEY,
        produit_id INT,
        utilisateur_id INT,
        message TEXT,                          
        note INT CHECK (note BETWEEN 1 AND 5),
        date_post DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits(id),
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        );
        
        CREATE TABLE commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER,
            produit_id INTEGER,  -- On stocke l'ID, pas le texte
            montant DECIMAL(10, 2),
            date_commande DATETIME DEFAULT CURRENT_TIMESTAMP,
            adresse_livraison TEXT,
            FOREIGN KEY(utilisateur_id) REFERENCES utilisateurs(id),
            FOREIGN KEY(produit_id) REFERENCES produits(id) 
        );
        -- Table Cartes de Recharge (Le Trésor caché)
        CREATE TABLE cartes_recharge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code_pin TEXT NOT NULL UNIQUE, -- Code à 12 chiffres
            montant DECIMAL(10, 2) NOT NULL,
            statut TEXT DEFAULT 'VALIDE', -- 'VALIDE' ou 'UTILISE'
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. INSERTION DES DONNÉES (SEED DATA)

    print("Insertion des données mauritaniennes...")

    # A. Utilisateurs
    # Note: Les mots de passe sont stockés ici direct en texte brut ou hash MD5 simulé
    # Pour le scénario, on utilise des hashs MD5 courants :
    # admin -> 21232f297a57a5a743894a0e4a801fc3
    # user  -> ee11cbb19052e40b07aac0ca060c23ee
    cursor.execute("""
        INSERT INTO utilisateurs (username, password, telephone, adresse, est_admin, solde_mru)
        VALUES 
        ('admin_baraka', '21232f297a57a5a743894a0e4a801fc3', '46123456', 'Bureau Direction, Tevragh-Zeina', 1, 500000.00),
        ('sidi_mauria', 'ee11cbb19052e40b07aac0ca060c23ee', '22334455', 'Arrêt Bus, Toujounine', 0, 200.00),
        ('etudiant_tp', 'password123', '36998877', 'Campus Universitaire', 0, 0.00)
    """)

    # B. Produits
    cursor.executescript("""
        INSERT INTO produits (nom, description, prix, quantite) VALUES 
        ('Thé Warka (1kg)', 'Le thé vert authentique pour le ataya du soir.', 150.00, 100),
        ('Boubou Bazin Riche (Getzner)', 'Bazin blanc qualité supérieure, importé.', 8000.00, 5),
        ('iPhone 15 Pro Max', '256GB, Titane Naturel. Garantie 1 an.', 48000.00, 3),
        ('Voile Melhfa Moderne', 'Tissu léger, motifs discrets.', 600.00, 20),
        ('Carte de Recharge Mauritel', 'Crédit téléphonique direct.', 200.00, 500);
    """)

    # C. Les Cartes de Recharge (Cible de l'Injection SQL)
    # L'étudiant doit trouver le code 829103847562
    cursor.executescript("""
        INSERT INTO cartes_recharge (code_pin, montant, statut) VALUES 
        ('829103847562', 5000.00, 'VALIDE'),
        ('102938475610', 1000.00, 'VALIDE'),
        ('445566778899', 200.00,  'UTILISE'),
        ('998877665544', 500.00,  'VALIDE');
    """)

    # Validation et fermeture
    connection.commit()
    connection.close()
    print("✅ Base de données 'elbaraka.db' initialisée avec succès !")


if __name__ == '__main__':
    init_db()