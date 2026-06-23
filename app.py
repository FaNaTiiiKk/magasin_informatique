from flask import Flask, render_template, request, redirect, session
import mysql.connector
import bcrypt
from flask_mail import Mail, Message
from datetime import date
import random

# Initialisation de l'application Flask
app = Flask(__name__)

# Clé secrète indispensable pour chiffrer et sécuriser les données de session (ex: le panier, l'ID client)
app.secret_key = 'une_cle_secrete_tres_complexe_a_changer'


# =========================================================================================
# ⚙️ CONFIGURATION ET CONFIGURATION DES EXTENSIONS
# =========================================================================================

# Configuration du serveur de messagerie (SMTP) pour l'envoi de mails automatiques
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True  # Active la sécurité TLS pour chiffrer la connexion avec le serveur mail
app.config['MAIL_USERNAME'] = 'votre_adresse_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'votre_mot_de_passe_d_application'  # Mot de passe sécurisé fourni par Google
app.config['MAIL_DEFAULT_SENDER'] = ('Magasin Informatique', 'votre_adresse_email@gmail.com')

# Initialisation de l'extension Mail avec les configurations définies ci-dessus
mail = Mail(app)


# =========================================================================================
# 💾 CONNEXION À LA BASE DE DONNÉES
# =========================================================================================

# Établissement de la connexion permanente avec la base de données MySQL locale
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="130321",
    database="magasin_informatique"
)

def get_db():
    """Fonction utilitaire pour renvoyer l'instance globale de la BDD"""
    return db


# =========================================================================================
# 🏠 ROUTE ACCUEIL
# =========================================================================================

@app.route("/")
def accueil():
    # Affiche simplement la page d'accueil du site (souvent avec les boutons Connexion/Inscription)
    return render_template("accueil.html")


# =========================================================================================
# 🔐 AUTHENTIFICATION (LOGIN)
# =========================================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    # Si l'utilisateur a soumis le formulaire de connexion
    if request.method == "POST":
        email = request.form["email"]      # Récupère l'email saisi dans le formulaire
        password = request.form["password"]  # Récupère le mot de passe saisi

        # Un curseur permet d'exécuter des requêtes SQL. 
        # dictionary=True : renvoie les résultats sous forme de dictionnaire (ex: client['nom'])
        # buffered=True : garde les résultats en mémoire pour éviter des conflits de lecture
        cursor = db.cursor(dictionary=True, buffered=True)

        # Sécurité : Compte administrateur d'urgence codé en dur (non sécurisé, utile en développement)
        if email == "admin" and password == "1234":
            cursor.close()
            return redirect("/admin")

        # Requête SQL sécurisée (%s) pour chercher si l'e-mail existe dans la table 'clients'
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        client = cursor.fetchone()  # Récupère la ligne correspondante (ou None s'il n'y a rien)
        cursor.close()

        # Si un client possède cet e-mail en BDD
        if client:
            # Récupère le mot de passe haché stocké en BDD et le convertit en tableau de bytes
            hashed_password_bdd = client['password'].encode('utf-8')
            # Convertit le mot de passe que l'utilisateur vient de taper en bytes
            password_saisi_bytes = password.encode('utf-8')

            # bcrypt.checkpw compare le mot de passe saisi avec le hash de la BDD
            if bcrypt.checkpw(password_saisi_bytes, hashed_password_bdd):
                
                # SÉCURITÉ : On vérifie si la colonne 'is_verified' est égale à 0 (compte non activé par mail)
                if client.get('is_verified') == 0:
                    return "Erreur login : Veuillez vérifier votre boîte mail et valider votre compte avant de vous connecter."
                
                # Connexion réussie : On stocke l'ID du client dans la session Flask
                session['client_id'] = client['id']
                # Redirection vers l'espace personnel du client
                return redirect(f"/client/{client['id']}")
            else:
                return "Erreur login (Mot de passe incorrect)"
        else:
            return "Erreur login (Email introuvable)"
            
    # Si la méthode est "GET", on affiche simplement le formulaire de connexion vierge
    return render_template("login.html")


# =========================================================================================
# 📝 ENREGISTREMENT (INSCRIPTION AVEC CODE DE VÉRIFICATION SIMULÉ)
# =========================================================================================

@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        # Récupération de l'ensemble des données du formulaire d'inscription
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]
        password = request.form["password"]
        telephone = request.form["telephone"]
        adresse = request.form["adresse"]

        # Politique de sécurité : Vérification de la longueur du mot de passe
        if len(password) < 12:
            return "Erreur : Le mot de passe doit contenir au moins 12 caractères."

        cursor = db.cursor(dictionary=True, buffered=True)

        # Vérification anti-doublon : On s'assure que l'e-mail n'est pas déjà pris
        cursor.execute("SELECT * FROM clients WHERE email=%s", (email,))
        compte_existant = cursor.fetchone()
        cursor.close()

        if compte_existant:
            return "Erreur : Cet email est déjà utilisé par un autre compte."

        # HACHAGE DU MOT DE PASSE
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        # GÉNÉRATION DU CODE DE VALIDATION SÉCURISÉ (4 chiffres)
        code_validation = str(random.randint(1000, 9999))

        # On stocke temporairement TOUTES les infos et le code dans la session Flask
        session['inscription_temp'] = {
            'nom': nom,
            'prenom': prenom,
            'email': email,
            'password': hashed_password,
            'telephone': telephone,
            'adresse': adresse,
            'code': code_validation
        }

        # On redirige vers la page où il devra taper le code
        return redirect("/verification")

    return render_template("inscription.html")


@app.route("/verification", methods=["GET", "POST"])
def verification():
    # Sécurité : Si l'utilisateur accède à la page sans avoir rempli le formulaire d'inscription
    if 'inscription_temp' not in session:
        return redirect("/inscription")

    infos = session['inscription_temp']
    code_attendu = infos['code']

    if request.method == "POST":
        code_saisi = request.form.get("code_saisi").strip()

        # Si le code est bon, on l'inscrit définitivement en BDD avec is_verified = 1
        if code_saisi == code_attendu:
            cursor = db.cursor(dictionary=True, buffered=True)
            try:
                cursor.execute("""
                    INSERT INTO clients (nom, prenom, email, password, telephone, adresse, is_verified) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (infos['nom'], infos['prenom'], infos['email'], infos['password'], infos['telephone'], infos['adresse'], 1))
                
                db.commit()
                
                # Inscription réussie : on nettoie la session temporaire
                session.pop('inscription_temp', None)
                return redirect("/login")

            except Exception as e:
                db.rollback()
                return f"Erreur lors de la validation finale : {e}"
            finally:
                cursor.close()
        else:
            # Code faux : on réaffiche la page avec une erreur
            return render_template("verification.html", code=code_attendu, erreur="Code incorrect. Veuillez réessayer.")

    # En GET : On affiche la page avec le code généré directement visible à l'écran
    return render_template("verification.html", code=code_attendu)


# =========================================================================================
# 👤 ESPACE CLIENT (HISTORIQUE DES COMMANDES / INTEGRÉ CORRIGÉ)
# =========================================================================================

@app.route("/client/<int:id_client>")
def client(id_client):
    # SÉCURITÉ : Vérifie si un utilisateur est connecté, et s'il essaie bien d'accéder à SON propre espace et pas celui d'un autre
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")
        
    cursor = db.cursor(dictionary=True, buffered=True)
    
    # 1. On va chercher les infos du client connecté (pour le "Bonjour Prenom Nom")
    cursor.execute("SELECT nom, prenom FROM clients WHERE id=%s", (id_client,))
    client_info = cursor.fetchone()
    
    # 2. Requête permettant de récupérer l'historique complet, incluant produits.stock et produits.id
    cursor.execute("""
        SELECT produits.id, produits.nom, produits.prix, produits.stock, details_commandes.quantite
        FROM commandes
        JOIN details_commandes ON commandes.id = details_commandes.id_commande
        JOIN produits ON produits.id = details_commandes.id_produit
        WHERE commandes.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()  # Récupère toutes les lignes trouvées
    cursor.close()
    
    # On transmet maintenant "client=client_info" pour éviter l'absence de l'objet dans Jinja2
    return render_template("client.html", produits=produits, id_client=id_client, client=client_info)


# =========================================================================================
# 🛍️ CATALOGUE / AJOUT D'UN ARTICLE AU PANIER
# =========================================================================================

@app.route("/client/<int:id_client>/commander", methods=["GET", "POST"])
def commander(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    cursor = db.cursor(dictionary=True, buffered=True)

    # Si le client visite la page (GET) : On lui affiche la liste des produits disponibles
    if request.method == "GET":
        cursor.execute("SELECT id, nom, prix, stock FROM produits")
        liste_produits = cursor.fetchall()
        cursor.close()
        return render_template("commander.html", id_client=id_client, produits=liste_produits)

    # Si le client clique sur "Ajouter au panier" (POST)
    if request.method == "POST":
        id_produit = request.form.get("id_produit")        # Récupère l'ID du produit choisi
        quantite_demandee = int(request.form.get("quantite")) # Récupère la quantité désirée

        # Vérification du stock en BDD
        cursor.execute("SELECT nom, stock FROM produits WHERE id=%s", (id_produit,))
        produit = cursor.fetchone()
        cursor.close()

        if not produit:
            return "Produit introuvable."

        # Sécurité : Empêche d'ajouter au panier s'il n'y a pas assez de stock physique en BDD
        if produit['stock'] < quantite_demandee:
            return f"Stock insuffisant ! Il ne reste que {produit['stock']} articles."

        # Initialisation du dictionnaire 'panier' dans la session s'il n'existe pas encore
        if 'panier' not in session:
            session['panier'] = {}
        
        panier = session['panier']
        
        # Structure du panier en session : { "id_produit": quantite }
        if id_produit in panier:
            panier[id_produit] += quantite_demandee  # Si déjà présent, on cumule la quantité
        else:
            panier[id_produit] = quantite_demandee   # Sinon, on crée la ligne dans le panier
            
        session.modified = True  # Indique expressément à Flask de sauvegarder les changements faits dans la session
        return redirect(f"/client/{id_client}/panier")


# =========================================================================================
# 🛒 GESTION DU PANIER (VUE ET SUPPRESSION)
# =========================================================================================

@app.route("/client/<int:id_client>/panier")
def voir_panier(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    panier = session.get('panier', {})  # Récupère le panier de la session (vide par défaut)
    liste_produits_panier = []          # Liste propre qu'on va envoyer au fichier HTML
    total_panier = 0                    # Calculateur du prix total cumulé

    # Si le panier contient des articles, on va chercher leurs détails réels (Nom, Prix) en BDD
    if panier:
        cursor = db.cursor(dictionary=True, buffered=True)
        for id_produit, quantite in panier.items():
            cursor.execute("SELECT id, nom, prix FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            
            if produit:
                subtotal = produit['prix'] * quantite  # Calcul du prix pour la ligne (Prix * Quantité)
                total_panier += subtotal              # Ajout au total général du panier
                # On ajoute toutes les infos calculées dans notre liste
                liste_produits_panier.append({
                    'id': produit['id'],
                    'nom': produit['nom'],
                    'prix': produit['prix'],
                    'quantite': quantite,
                    'sous_total': subtotal
                })
        cursor.close()

    return render_template("panier.html", id_client=id_client, panier=liste_produits_panier, total=total_panier)


@app.route("/client/<int:id_client>/panier/supprimer/<id_produit>")
def supprimer_du_panier(id_client, id_produit):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    # Si le panier existe bien
    if 'panier' in session:
        panier = session['panier']
        # Si l'ID du produit sélectionné est trouvé dans le dictionnaire, on le retire (.pop())
        if id_produit in panier:
            panier.pop(id_produit)
            session.modified = True  # Sauvegarde la modification de session

    # Redirection instantanée vers le panier rafraîchi (l'article aura disparu et le total aura baissé)
    return redirect(f"/client/{id_client}/panier")


# =========================================================================================
# 📋 CONFIRMATION INTERMÉDIAIRE DU PANIER (RÉCAPITULATIF)
# =========================================================================================

@app.route("/client/<int:id_client>/panier/confirmation")
def confirmation_panier(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    panier = session.get('panier', {})
    if not panier:
        return redirect(f"/client/{id_client}/panier")

    cursor = db.cursor(dictionary=True, buffered=True)
    
    # Grande utilité de cette page intermédiaire : Aller lire l'adresse et le téléphone du client en BDD
    # afin de lui afficher un récapitulatif de livraison avant qu'il ne clique sur "Payer"
    cursor.execute("SELECT nom, prenom, adresse, telephone FROM clients WHERE id=%s", (id_client,))
    client_info = cursor.fetchone()

    liste_produits_panier = []
    total_panier = 0
    
    # Recalcul des sous-totaux et liste des articles pour l'affichage final
    for id_produit, quantite in panier.items():
        cursor.execute("SELECT nom, prix FROM produits WHERE id=%s", (id_produit,))
        produit = cursor.fetchone()
        if produit:
            subtotal = produit['prix'] * quantite
            total_panier += subtotal
            liste_produits_panier.append({
                'nom': produit['nom'],
                'prix': produit['prix'],
                'quantite': quantite,
                'sous_total': subtotal
            })
            
    cursor.close()
    # Envoi de l'ensemble des données (Panier + Profil de livraison) au template confirmation.html
    return render_template("confirmation.html", id_client=id_client, panier=liste_produits_panier, total=total_panier, client=client_info)


# =========================================================================================
# 🚀 FINALISATION DE LA COMMANDE (BDD + DÉDUCTION STOCKS)
# =========================================================================================

@app.route("/client/<int:id_client>/panier/finaliser")
def finaliser_panier(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    panier = session.get('panier', {})
    if not panier:
        return "Votre panier est vide."

    cursor = db.cursor(dictionary=True, buffered=True)

    try:
        # SÉCURITÉ CRITIQUE ANTI-CONCURRENCE : 
        # On vérifie une toute dernière fois les stocks réels juste avant d'écrire en BDD, 
        # au cas où un autre utilisateur aurait acheté le même produit entre-temps.
        for id_produit, quantite_demandee in panier.items():
            cursor.execute("SELECT nom, stock FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            if not produit or produit['stock'] < quantite_demandee:
                cursor.close()
                return f"Erreur : Le produit '{produit['nom'] if produit else 'Inconnu'}' n'a plus assez de stock."

        # 1. ÉCRITURE DE L'EN-TÊTE : On crée une ligne dans la table 'commandes' pour ce client à la date d'aujourd'hui (NOW())
        cursor.execute("INSERT INTO commandes (id_client, date_commande) VALUES (%s, NOW())", (id_client,))
        id_commande = cursor.lastrowid  # Récupère l'ID unique (clé primaire automatique) de la commande qu'on vient de générer
        
        # 2. ÉCRITURE DES DÉTAILS : On boucle sur chaque article du panier en session
        for id_produit, quantite_demandee in panier.items():
            cursor.execute("SELECT prix FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            prix_unitaire = produit['prix']
            
            # Insertion dans la table pivot 'details_commandes' reliée à l'ID de notre commande globale
            cursor.execute(
                "INSERT INTO details_commandes (id_commande, id_produit, quantite, prix_unitaire) VALUES (%s, %s, %s, %s)", 
                (id_commande, id_produit, quantite_demandee, prix_unitaire)
            )
            
            # 3. MISE À JOURS DU STOCK PRODUIT : On déduit la quantité achetée directement du stock de la table 'produits'
            cursor.execute("UPDATE produits SET stock = stock - %s WHERE id=%s", (quantite_demandee, id_produit))
            
        # Si tout s'est bien passé sans plantage, on valide définitivement l'ensemble de la transaction SQL
        db.commit()
        
        # On vide le panier de la session utilisateur puisqu'il est désormais enregistré de manière permanente en BDD
        session.pop('panier', None) 
        
    except Exception as e:
        # En cas d'erreur ou de coupure durant la boucle d'insertion, le rollback annule TOUT ce qui a été fait dans le bloc try. 
        # Sécurité : cela évite d'avoir une commande à moitié enregistrée ou des stocks faussés.
        db.rollback()
        return f"Erreur lors de la finalisation : {e}"
    finally:
        cursor.close()

    # Redirection finale vers l'espace client (où le client pourra voir son historique d'achats actualisé)
    return redirect(f"/client/{id_client}")


# =========================================================================================
# 💳 PROCESSUS DE PAIEMENT SÉCURISÉ ET VALIDATION DE COMMANDE
# =========================================================================================

@app.route("/paiement/<int:id_client>", methods=["GET", "POST"])
def paiement(id_client):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    # 1. On récupère le panier depuis la SESSION Flask au lieu de la table SQL
    panier = session.get('panier', {})
    liste_produits_panier = []
    total_panier = 0

    cursor = db.cursor(dictionary=True, buffered=True)
    
    # 2. Si le panier en session contient des produits, on va chercher leurs infos en BDD (Nom, Prix, Stock)
    if panier:
        for id_produit, quantite in panier.items():
            cursor.execute("SELECT id, nom, prix, stock FROM produits WHERE id=%s", (id_produit,))
            produit = cursor.fetchone()
            if produit:
                subtotal = produit['prix'] * quantite
                total_panier += subtotal
                liste_produits_panier.append({
                    'id_produit': produit['id'],
                    'nom': produit['nom'],
                    'prix': produit['prix'],
                    'stock': produit['stock'],
                    'quantite': quantite,
                    'total': subtotal
                })

    if request.method == "POST":
        nom = request.form["nom"].strip()
        numero = request.form["numero"].replace(" ", "").replace("-", "")
        expiration = request.form["expiration"].strip()
        cvv = request.form["cvv"].strip()
        
        # Vérification de sécurité : Panier vide
        if not liste_produits_panier:
            cursor.close()
            return render_template(
                "paiement.html",
                id_client=id_client,
                produits=liste_produits_panier,
                total_panier=total_panier,
                erreur="Votre panier est vide."
            )
        
        # Validation des données de la carte bancaire (Simulation bancaire)
        if not nom or not numero.isdigit() or len(numero) != 16 or not expiration or not cvv.isdigit() or len(cvv) not in (3, 4):
            cursor.close()
            return render_template(
                "paiement.html",
                id_client=id_client,
                produits=liste_produits_panier,
                total_panier=total_panier,
                erreur="Paiement refusé : vérifiez les informations de la carte."
            )
        
        # Contrôle ultime des stocks physiques en BDD avant transaction
        for produit in liste_produits_panier:
            if produit["stock"] < produit["quantite"]:
                cursor.close()
                return render_template(
                    "paiement.html",
                    id_client=id_client,
                    produits=liste_produits_panier,
                    total_panier=total_panier,
                    erreur=f"Stock insuffisant pour {produit['nom']}."
                )
        
        # 1. Écriture en base de données : Enregistrement de la commande principale
        cursor.execute("""
            INSERT INTO commandes (id_client, date_commande, total, statut)
            VALUES (%s, NOW(), %s, %s)
        """, (id_client, total_panier, "Validée"))
        id_commande = cursor.lastrowid
        
        # 2. Boucle d'enregistrement des détails de la commande et mise à jour des stocks
        for produit in liste_produits_panier:
            cursor.execute("""
                INSERT INTO details_commandes (id_commande, id_produit, quantite, prix_unitaire)
                VALUES (%s, %s, %s, %s)
            """, (id_commande, produit["id_produit"], produit["quantite"], produit["prix"]))
            
            cursor.execute("""
                UPDATE produits
                SET stock = stock - %s
                WHERE id = %s
            """, (produit["quantite"], produit["id_produit"]))
            
        # 3. Nettoyage final : On valide les écritures SQL et on vide le panier de la session
        db.commit()
        cursor.close()
        session.pop('panier', None)
        
        # Redirection et affichage sur le template finalisation
        return render_template(
            "finalisation.html",
            nom=nom,
            id_client=id_client,
            id_commande=id_commande,
            total_panier=total_panier,
            carte=numero[-4:]
        )
        
    cursor.close()
    return render_template(
        "paiement.html",
        id_client=id_client,
        produits=liste_produits_panier,
        total_panier=total_panier
    )

# =========================================================================================
# 🏁 POINT D'ENTRÉE APPLICATION
# =========================================================================================

if __name__ == '__main__':
    print("Le serveur Flask démarre sur http://127.0.0.1:5000 ...")
    # Lancement du serveur local avec le mode "debug=True" (permet le rechargement automatique du code à chaque sauvegarde)
    app.run(host="127.0.0.1", port=5000, debug=True)