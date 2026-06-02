from flask import Flask, render_template, request, redirect, session

import mysql.connector

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

        if email == "admin" and password == "1234":
            return redirect("/admin")

        cursor.execute("SELECT * FROM clients WHERE email=%s AND password=%s", (email, password))
        client = cursor.fetchone()
        cursor.close()

        if client:
            session['client_id'] = client['id']
            return redirect(f"/client/{client['id']}")
        else:
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
    return render_template("client.html", produits=produits)

# COMMANDE
@app.route("/client/<int:id_client>/commander/<int:id_produit>", methods=["POST"])
def commander(id_client, id_produit):
    if 'client_id' not in session or session['client_id'] != id_client:
        return redirect("/login")

    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT stock FROM produits WHERE id=%s", (id_produit,))
    produit = cursor.fetchone()
    
    if not produit or produit['stock'] <= 0:
        cursor.close()
        return "Produit indisponible"

    try:
        cursor.execute("INSERT INTO commandes (id_client) VALUES (%s)", (id_client,))
        id_commande = cursor.lastrowid
        
        cursor.execute("INSERT INTO details_commandes (id_commande, id_produit, quantite) VALUES (%s, %s, 1)", 
                       (id_commande, id_produit))
        
        cursor.execute("UPDATE produits SET stock = stock - 1 WHERE id=%s", (id_produit,))
        
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Erreur lors de la commande : {e}"
    finally:
        cursor.close()

    return redirect(f"/client/{id_client}")

if __name__ == '__main__':
    app.run(debug=True)