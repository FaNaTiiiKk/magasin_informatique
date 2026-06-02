from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Connexion BDD
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="130321",  # Mets "Password123!" ou ton mot de passe si tu en as défini un
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
        
        # ADMIN
        if email == "admin" and password == "1234":
            return redirect("/admin")
            
        # CLIENT
        cursor.execute(
            "SELECT * FROM clients WHERE email=%s AND password=%s",
            (email, password)
        )
        client = cursor.fetchone()
        
        if client:
            return redirect(f"/client/{client['id']}")
        else:
            return "Erreur login"
            
    return render_template("login.html")

# PAGE CLIENT
@app.route("/client/<int:id_client>")
def client(id_client):
    cursor = db.cursor(dictionary=True, buffered=True)
    
    cursor.execute("""
        SELECT produits.nom, produits.prix, commandes.quantite
        FROM commandes
        JOIN produits ON produits.id = commandes.id_produit
        WHERE commandes.id_client = %s
    """, (id_client,))
    produits = cursor.fetchall()
    cursor.close()
    return render_template("client.html", produits=produits)

if __name__ == '__main__':
    app.run(debug=True)