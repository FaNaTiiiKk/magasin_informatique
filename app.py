from flask import Flask, render_template, request, redirect, session
import mysql.connector
# AJOUT : Importation des outils de hachage sécurisés de Werkzeug
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_tres_complexe_a_changer'

# Connexion BDD
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="130321",
    database="magasin_informatique"
)

# ACCUEIL
@app.route("/")
def accueil():
    return render_template("accueil.html")

# LOGIN (Modifié pour la migration des mots de passe en clair à la volée)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cursor = db.cursor(dictionary=True, buffered=True)

        # Compte admin statique (Inchangé)
        if email == "admin" and password == "1234":
            return redirect("/admin")

        # 1. On cherche d'abord l'utilisateur UNIQUEMENT par son email
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        client = cursor.fetchone()

        if client:
            password_bdd = client['password']

            # 2. Détecter si le mot de passe en BDD est déjà haché
            # Les hashs de Werkzeug commencent par un préfixe d'algorithme (ex: 'scrypt:', 'pbkdf2:')
            is_hashed = password_bdd.startswith(('scrypt:', 'pbkdf2:', 'bcrypt'))

            if not is_hashed:
                # ─── CAS 1 : Le mot de passe en BDD est encore en clair ───
                if password == password_bdd:
                    # Le mot de passe saisi est correct. On génère un hash sécurisé.
                    new_hash = generate_password_hash(password)
                    
                    # On met à jour la ligne du client pour remplacer le texte en clair par le hash
                    cursor.execute("UPDATE clients SET password=%s WHERE id=%s", (new_hash, client['id']))
                    db.commit() # Très important pour valider la modification en BDD
                    cursor.close()

                    # Connexion et redirection vers l'espace client
                    session['client_id'] = client['id']
                    return redirect(f"/client/{client['id']}")
                else:
                    cursor.close()
                    return "Erreur login"
            else:
                # ─── CAS 2 : Le mot de passe en BDD est déjà haché sécurisé ───
                cursor.close()
                if check_password_hash(password_bdd, password):
                    session['client_id'] = client['id']
                    return redirect(f"/client/{client['id']}")
                else:
                    return "Erreur login"
        else:
            cursor.close()
            return "Erreur login"

    return render_template("login.html")

# PAGE CLIENT
@app.route("/client/<int:id_client>")
def client(id_client):
    # Vérification de sécurité
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")
        
    cursor = db.cursor(dictionary=True, buffered=True)
    cursor.execute("""
        SELECT produits.nom, produits.prix, details_commandes.quantite
        FROM commandes
        JOIN details_commandes ON commandes.id = details_commandes.id_commande
        JOIN produits ON produits.id = details_commandes.id_produit
        WHERE commandes.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    cursor.close()
    
    return render_template("client.html", produits=produits, id_client=id_client)

# COMMANDE
@app.route("/client/<int:id_client>/commander", methods=["GET", "POST"])
def commander(id_client):
    # Vérification de sécurité
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    cursor = db.cursor(dictionary=True, buffered=True)

    # Si le client arrive sur la page (GET)
    if request.method == "GET":
        cursor.execute("SELECT id, nom, prix, stock FROM produits")
        liste_produits = cursor.fetchall()
        cursor.close()
        return render_template("commander.html", id_client=id_client, produits=liste_produits)

    # Si le client valide le formulaire (POST)
    if request.method == "POST":
        id_produit = request.form.get("id_produit")
        quantite_demandee = int(request.form.get("quantite"))

        # 1- Vérifier le stock et récupérer le prix du produit
        cursor.execute("SELECT prix, stock FROM produits WHERE id=%s", (id_produit,))
        produit = cursor.fetchone()

        if not produit:
            cursor.close()
            return "Produit introuvable."

        if produit['stock'] < quantite_demandee:
            cursor.close()
            return f"Stock insuffisant ! Il ne reste que {produit['stock']} articles."

        prix_unitaire = produit['prix']

        try:
            # 2- Créer une commande
            cursor.execute(
                "INSERT INTO commandes (id_client, date_commande) VALUES (%s, NOW())", 
                (id_client,)
            )
            id_commande = cursor.lastrowid
            
            # 3- Ajouter le détail
            cursor.execute(
                "INSERT INTO details_commandes (id_commande, id_produit, quantite, prix_unitaire) VALUES (%s, %s, %s, %s)", 
                (id_commande, id_produit, quantite_demandee, prix_unitaire)
            )
            
            # 4- Diminuer le stock
            cursor.execute("UPDATE produits SET stock = stock - %s WHERE id=%s", (quantite_demandee, id_produit))
            
            db.commit()
        except Exception as e:
            db.rollback()
            return f"Erreur lors de la commande : {e}"
        finally:
            cursor.close()

        return redirect(f"/client/{id_client}")

# Bloc de démarrage 
if __name__ == '__main__':
    print("Le serveur Flask démarre sur http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)