from flask import Flask, render_template, request, redirect, session
import mysql.connector
import bcrypt
# MODIFICATION : Importation de Flask-Mail pour l'envoi de e-mails
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'une_cle_secrete_tres_complexe_a_changer'

# MODIFICATION : Configuration de Flask-Mail (Exemple avec Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'votre_adresse_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe_d_application'
app.config['MAIL_DEFAULT_SENDER'] = ('Magasin Informatique', 'votre_adresse_email@gmail.com')

# Initialisation globale de l'extension Mail
mail = Mail(app)

# Connexion BDD globale (Variable "db" bien définie à la racine)
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

        # On cherche l'utilisateur UNIQUEMENT par son email
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        client = cursor.fetchone()
        cursor.close()

        if client:
            hashed_password_bdd = client['password'].encode('utf-8')
            password_saisi_bytes = password.encode('utf-8')

            if bcrypt.checkpw(password_saisi_bytes, hashed_password_bdd):
                # SÉCURITÉ : Bloquer si l'adresse e-mail n'est pas encore validée
                if client.get('is_verified') == 0:
                    return "Erreur login : Veuillez vérifier votre boîte mail et valider votre compte avant de vous connecter."
                
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
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]
        password = request.form["password"]
        telephone = request.form["telephone"]
        adresse = request.form["adresse"]

        # VÉRIFICATION : Minimum 12 caractères
        if len(password) < 12:
            return "Erreur : Le mot de passe doit contenir au moins 12 caractères."

        cursor = db.cursor(dictionary=True, buffered=True)

        # Vérifier si l'email existe déjà
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        compte_existant = cursor.fetchone()

        if compte_existant:
            cursor.close()
            return "Erreur : Cet email est déjà utilisé par un autre compte."

        # Hachage du mot de passe
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # Insertion avec is_verified initialisé à 0
        try:
            cursor.execute("""
                INSERT INTO clients (nom, prenom, email, password, telephone, adresse, is_verified) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nom, prenom, email, hashed_password, telephone, adresse, 0))
            
            db.commit()
            
            # Envoi du mail de confirmation d'inscription
            try:
                msg = Message(
                    subject="Confirmation de votre inscription !",
                    recipients=[email]
                )
                msg.body = f"Bonjour {prenom},\n\nVotre inscription sur notre site de Magasin Informatique a bien été validée.\n\nMerci pour votre confiance !\nL'équipe de support."
                mail.send(msg)
            except Exception as mail_error:
                print(f"Erreur lors de l'envoi du mail : {mail_error}")

        except Exception as e:
            db.rollback()
            return f"Erreur lors de l'inscription : {e}"
        finally:
            cursor.close()

        return redirect("/login")

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

# SUPPRIMER UN ARTICLE DU PANIER
@app.route("/client/<int:id_client>/panier/supprimer/<id_produit>")
def supprimer_du_panier(id_client, id_produit):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    # On vérifie si le panier existe en session
    if 'panier' in session:
        panier = session['panier']
        # Si le produit est bien dans le panier, on le supprime
        if id_produit in panier:
            panier.pop(id_produit)
            # On signale à Flask que la session a été modifiée
            session.modified = True

    # On redirige l'utilisateur vers la page du panier mis à jour
    return redirect(f"/client/{id_client}/panier")

# ENREGISTRER UN ACHAT DANS LE PANIER TEMPORAIRE
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

        cursor.execute("SELECT nom, stock FROM produits WHERE id=%s", (id_produit,))
        produit = cursor.fetchone()
        cursor.close()

        if not produit:
            return "Produit introuvable."

        if produit['stock'] < quantite_demandee:
            return f"Stock insuffisant ! Il ne reste que {produit['stock']} articles."

        if 'panier' not in session:
            session['panier'] = {}
        
        panier = session['panier']
        
        if id_produit in panier:
            panier[id_produit] += quantite_demandee
        else:
            panier[id_produit] = quantite_demandee
            
        session.modified = True
        return redirect(f"/client/{id_client}/panier")

# VUE DU PANIER
@app.route("/client/<int:id_client>/panier")
def voir_panier(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    panier = session.get('panier', {})
    liste_produits_panier = []
    total_panier = 0

    if panier:
        cursor = db.cursor(dictionary=True, buffered=True)
        for id_produit, quantite in panier.items():
            cursor.execute("SELECT id, nom, prix FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            
            if produit:
                subtotal = produit['prix'] * quantite
                total_panier += subtotal
                liste_produits_panier.append({
                    'id': produit['id'],
                    'nom': produit['nom'],
                    'prix': produit['prix'],
                    'quantite': quantite,
                    'sous_total': subtotal
                })
        cursor.close()

    return render_template("panier.html", id_client=id_client, panier=liste_produits_panier, total=total_panier)

# PAGE INTERMÉDIAIRE : CONFIRMATION DES INFOS & ARTICLES (CORRIGÉE)
@app.route("/client/<int:id_client>/panier/confirmation")
def confirmation_panier(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    panier = session.get('panier', {})
    if not panier:
        return redirect(f"/client/{id_client}/panier")

    cursor = db.cursor(dictionary=True, buffered=True)
    
    # Récupération des informations de profil du client pour livraison
    cursor.execute("SELECT nom, prenom, adresse, telephone FROM clients WHERE id=%s", (id_client,))
    client_info = cursor.fetchone()

    liste_produits_panier = []
    total_panier = 0
    
    for id_produit, quantite in panier.items():
        cursor.execute("SELECT nom, prix FROM produits WHERE id=%s", (id_produit,))
        produit = cursor.fetchone()
        if produit:
            # CORRECTION DE LA FAUTE DE FRAPPE ICI
            subtotal = produit['prix'] * quantite
            total_panier += subtotal
            liste_produits_panier.append({
                'nom': produit['nom'],
                'prix': produit['prix'],
                'quantite': quantite,
                'sous_total': subtotal
            })
            
    cursor.close()
    return render_template("confirmation.html", id_client=id_client, panier=liste_produits_panier, total=total_panier, client=client_info)

# ACTION FINALE : ENREGISTREMENT BDD ET VIDAGE DE SESSION
@app.route("/client/<int:id_client>/panier/finaliser")
def finaliser_panier(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    panier = session.get('panier', {})
    if not panier:
        return "Votre panier est vide."

    cursor = db.cursor(dictionary=True, buffered=True)

    try:
        # Contrôle des stocks réels
        for id_produit, quantite_demandee in panier.items():
            cursor.execute("SELECT nom, stock FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            if not produit or produit['stock'] < quantite_demandee:
                cursor.close()
                return f"Erreur : Le produit '{produit['nom'] if produit else 'Inconnu'}' n'a plus assez de stock."

        # Création de l'en-tête de commande
        cursor.execute("INSERT INTO commandes (id_client, date_commande) VALUES (%s, NOW())", (id_client,))
        id_commande = cursor.lastrowid
        
        # Injection des lignes et mise à jour des stocks
        for id_produit, quantite_demandee in panier.items():
            cursor.execute("SELECT prix FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            prix_unitaire = produit['prix']
            
            cursor.execute(
                "INSERT INTO details_commandes (id_commande, id_produit, quantite, prix_unitaire) VALUES (%s, %s, %s, %s)", 
                (id_commande, id_produit, quantite_demandee, prix_unitaire)
            )
            cursor.execute("UPDATE produits SET stock = stock - %s WHERE id=%s", (quantite_demandee, id_produit))
            
        db.commit()
        session.pop('panier', None) # Libération du panier
        
    except Exception as e:
        db.rollback()
        return f"Erreur lors de la finalisation : {e}"
    finally:
        cursor.close()

    return redirect(f"/client/{id_client}")

if __name__ == '__main__':
    print("Le serveur Flask démarre sur http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)