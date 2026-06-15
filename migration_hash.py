import mysql.connector
import bcrypt

# Configuration de la connexion à la base de données
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="130321",
    database="magasin_informatique"
)

def migrate_passwords():
    # Utilisation directe de la connexion globale 'db'
    cursor = db.cursor(dictionary=True)
    
    # AJOUT SÉCURITÉ : On sélectionne UNIQUEMENT les mots de passe qui ne commencent PAS par $2
    # Cela évite de hacher deux fois un mot de passe déjà sécurisé en Bcrypt
    cursor.execute("SELECT id, email, password FROM clients WHERE password NOT LIKE '$2%'")
    clients = cursor.fetchall()
    
    if not clients:
        print("Aucun client à migrer. Tous les mots de passe sont déjà sécurisés !")
        cursor.close()
        return

    print(f"Début de la migration de {len(clients)} client(s)...")
    
    for client in clients:
        password_clair = client['password'].encode('utf-8')
        
        # Générer un hash Bcrypt robuste (rounds=12 est la valeur standard recommandée)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_clair, salt)
        
        # Mettre à jour la base de données
        cursor.execute(
            "UPDATE clients SET password = %s WHERE id = %s",
            (hashed.decode('utf-8'), client['id'])
        )
        print(f"-> Client {client['email']} migré avec succès.")
    
    # Validation des modifications dans MySQL
    db.commit()
    cursor.close()
    print("Migration terminée avec succès !")

if __name__ == "__main__":
    try:
        migrate_passwords()
    except Exception as e:
        print(f"Une erreur est survenue lors de la migration : {e}")
    finally:
        # Fermeture propre de la connexion globale
        if db.is_connected():
            db.close()