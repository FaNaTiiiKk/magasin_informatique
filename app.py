from flask import Flask, render_template, request, redirect, session
import mysql.connector
# IMPORTATION : On ajoute la bibliothèque bcrypt pour vérifier le mot de passe
import bcrypt

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

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cursor = db.cursor(dictionary=True, buffered=True)

        # Compte admin de secours (en clair)
        if email == "admin" and password == "1234":
            cursor.close()
            return redirect("/admin")

        # MODIFICATION 1 : On cherche l'utilisateur UNIQUEMENT par son email
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        client = cursor.fetchone()
        cursor.close()

        if client:
            # On récupère le mot de passe haché de la BDD et on le convertit en bytes
            hashed_password_bdd = client['password'].encode('utf-8')
            # On convertit le mot de passe saisi en clair par l'utilisateur en bytes
            password_saisi_bytes = password.encode('utf-8')

            # MODIFICATION 2 : On utilise bcrypt pour comparer le mot de passe en clair et le hash
            if bcrypt.checkpw(password_saisi_bytes, hashed_password_bdd):
                session['client_id'] = client['id']
                return redirect(f"/client/{client['id']}")
            else:
                return "Erreur login (Mot de passe incorrect)"
        else:
            return "Erreur login (Email introuvable)"
            
    return render_template("login.html")

# INSCRIPTION (SIGN UP)
@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        # Récupération des données du formulaire HTML
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]
        password = request.form["password"]
        telephone = request.form["telephone"]
        adresse = request.form["adresse"]

        # VÉRIFICATION DE SÉCURITÉ : Minimum 12 caractères
        if len(password) < 12:
            return "Erreur : Le mot de passe doit contenir au moins 12 caractères."

        cursor = db.cursor(dictionary=True, buffered=True)

        # 1. Vérifier si l'email existe déjà dans la base de données
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        compte_existant = cursor.fetchone()

        if compte_existant:
            cursor.close()
            return "Erreur : Cet email est déjà utilisé par un autre compte."

        # 2. Hachage du mot de passe avec bcrypt
        password_bytes = password.encode('utf-8')  # Conversion de la chaîne en bytes
        salt = bcrypt.gensalt()                     # Génération du sel de sécurité
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8') # Hachage et conversion en chaîne de caractères

        # 3. Insertion du nouveau client dans la table 'clients'
        try:
            cursor.execute("""
                INSERT INTO clients (nom, prenom, email, password, telephone, adresse) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nom, prenom, email, hashed_password, telephone, adresse))
            
            db.commit() # Validation de l'insertion en BDD
        except Exception as e:
            db.rollback() # En cas d'erreur de base de données, on annule
            return f"Erreur lors de l'inscription : {e}"
        finally:
            cursor.close()

        # Redirection automatique vers la page de connexion après inscription réussie
        return redirect("/login")

    # Si la requête est en GET (accès direct à l'URL), on affiche le formulaire
    return render_template("inscription.html")

# PAGE CLIENT
@app.route("/client/<int:id_client>")
def client(id_client):
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
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    cursor = db.cursor(dictionary=True, buffered=True)

    if request.method == "GET":
        cursor.execute("SELECT id, nom, prix, stock FROM produits")
        liste_produits = cursor.fetchall()
        cursor.close()
        return render_template("commander.html", id_client=id_client, produits=liste_produits)

    if request.method == "POST":
        id_produit = request.form.get("id_produit")
        quantite_demandee = int(request.form.get("quantite"))

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
            cursor.execute(
                "INSERT INTO commandes (id_client, date_commande) VALUES (%s, NOW())", 
                (id_client,)
            )
            id_commande = cursor.lastrowid
            
            cursor.execute(
                "INSERT INTO details_commandes (id_commande, id_produit, quantite, prix_unitaire) VALUES (%s, %s, %s, %s)", 
                (id_commande, id_produit, quantite_demandee, prix_unitaire)
            )
            
            cursor.execute("UPDATE produits SET stock = stock - %s WHERE id=%s", (quantite_demandee, id_produit))
            db.commit()
        except Exception as e:
            db.rollback()
            return f"Erreur lors de la commande : {e}"
        finally:
            cursor.close()

        return redirect(f"/client/{id_client}")

if __name__ == '__main__':
    print("Le serveur Flask démarre sur http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)