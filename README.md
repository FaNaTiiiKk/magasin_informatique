# 🛒 Magasin Informatique - E-commerce Web App

A dynamic e-commerce web application built with Flask and MySQL. This project simulates a computer hardware store, featuring user authentication, shopping cart management, a checkout system with shipping review, and simulated secure payment.

---

## ✨ Features

* **User Authentication:** Secure signup with password hashing (bcrypt) and simulated account verification via a 4-digit security code.
* **Shopping Cart:** Temporary items management handled smoothly through Flask browser sessions.
* **Checkout & Payment:** Order summary, shipping address handling, and a custom-designed secure credit card payment simulation.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.8+, Flask
* **Database:** MySQL Server
* **Frontend:** HTML5, CSS3 (Custom responsive UI)
* **Tools:** MySQL Workbench

---

## 🚀 Getting Started

### Prerequisites

Before starting, ensure you have the following installed on your machine:
* Python 3.8+
* MySQL Server
* MySQL Workbench

### Installation & Run

1. Clone the repository and navigate to the project directory:

```bash
git clone [https://github.com/FaNaTiiiKk/magasin_informatique.git](https://github.com/FaNaTiiiKk/magasin_informatique.git)
cd magasin_informatique

2. Create and activate a virtual environment:

# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS / Linux
python3 -m venv venv
source venv/bin/activate

3. Install the required Python dependencies:

pip install flask mysql-connector-python bcrypt flask-mail

4. Database Setup (MySQL):
Open MySQL Workbench, connect to your local server, and execute the following initialization script to build the schema:

```text
```sql
DROP DATABASE IF EXISTS magasin_informatique;
CREATE DATABASE magasin_informatique;
USE magasin_informatique;

CREATE TABLE clients (
    id INT AUTO_INCREMENT,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    adresse VARCHAR(150),
    telephone VARCHAR(20),
    is_verified TINYINT(1) DEFAULT 0,
    PRIMARY KEY (id)
);

CREATE TABLE produits (
    id INT AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    prix DECIMAL(10,2) NOT NULL DEFAULT 0,
    stock INT NOT NULL DEFAULT 0,
    image VARCHAR(100),
    PRIMARY KEY (id),
    CHECK (prix >= 0),
    CHECK (stock >= 0)
);

CREATE TABLE commandes (
    id INT AUTO_INCREMENT,
    id_client INT NOT NULL,
    date_commande DATE NOT NULL,
    total DECIMAL(10,2) DEFAULT 0,
    statut VARCHAR(30) DEFAULT 'En attente',
    PRIMARY KEY (id),
    FOREIGN KEY (id_client) REFERENCES clients(id)
);

CREATE TABLE details_commandes (
    id INT AUTO_INCREMENT,
    id_commande INT NOT NULL,
    id_produit INT NOT NULL,
    quantite INT NOT NULL,
    prix_unitaire DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (id_commande) REFERENCES commandes(id),
    FOREIGN KEY (id_produit) REFERENCES produits(id),
    CHECK (quantite > 0)
);

CREATE TABLE panier (
    id INT AUTO_INCREMENT,
    id_client INT NOT NULL,
    id_produit INT NOT NULL,
    quantite INT NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    FOREIGN KEY (id_client) REFERENCES clients(id),
    FOREIGN KEY (id_produit) REFERENCES produits(id),
    UNIQUE (id_client, id_produit),
    CHECK (quantite > 0)
);

5. Configure Database Credentials:
Open app.py and update the MySQL connection block with your local setup:

```text
```python
db = mysql.connector.connect(
    host="localhost",
    user="YOUR_MYSQL_USER",
    password="YOUR_MYSQL_PASSWORD",
    database="magasin_informatique"
)

6. Start the Local Server:

python app.py

---

## 🌐 Access Points

Once the application server is running, access it via your web browser:
* Main Web Application: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🧪 Testing the Application

* 📝 **Simulated Mail Verification:** During registration, a 4-digit security code is displayed directly on the screen for development purposes. Enter this code to immediately set the account status to is_verified = 1 in the database.
* 💳 **Checkout Simulation:** Browse the catalogue, add hardware items to your cart, and head over to the payment page. You can input any simulated dummy credit card credentials to successfully complete and generate your order receipt.

---

## 📁 Project Structure

```text
magasin_informatique/
├── app.py                 # Main Flask application and backend routing logic
├── static/
│   ├── style.css          # Global unified stylesheet
│   └── fond.jpg           # Application background image
└── templates/             # HTML UI templates
    ├── inscription.html   # Account registration form
    ├── verification.html  # Security code validation screen
    ├── paiement.html      # Credit card payment checkout form
    └── finalisation.html  # Order invoice and payment success screen