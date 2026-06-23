# 🛒 Application E-Commerce Flask #

Ce projet est une application web e-commerce dynamique développée en Python avec le framework Flask et une base de données MySQL. Elle intègre un catalogue de produits, un système de panier d'achat géré en session, un tunnel de commande avec récapitulatif de livraison, et une simulation de paiement sécurisé.

---

Architecture simplifiée du projet

├── app.py                 # Serveur Flask & Logique Backend (Routes, SQL, Sessions)
├── static/
│   ├── style.css          # Feuille de style CSS globale (Design unifié)
│   └── fond.jpg           # Image de fond pour la page d'accueil
└── templates/             # Pages HTML du projet
    ├── inscription.html   # Formulaire de création de compte
    ├── verification.html  # Écran de validation par code de sécurité
    ├── paiement.html      # Formulaire de carte bancaire (Design Carte)
    └── finalisation.html  # Reçu de paiement et succès de la commande

## Prérequis ##

Avant de commencer, assurez-vous d'avoir installé sur votre machine :
* [Python 3.8+](https://www.python.org/)
* [MySQL Server](https://dev.mysql.com/downloads/mysql/)
* [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) (recommandé pour la gestion visuelle de la BDD)

---

## Installation et Configuration ##

Suivez pas à pas les étapes ci-dessous pour cloner, installer et lancer le projet dans votre environnement local.

### 1. Récupérer le projet ###

git clone https://github.com/FaNaTiiiKk/magasin_informatique.git
cd magasin_informatique

### 2. Créer et activer un environnement Virtuel ###

# Sur Windows
python -m venv venv
venv\Scripts\activate

# Sur macOS / Linux
python3 -m venv venv
source venv/bin/activate

### 3. Installer les dépendances Python ###

pip install flask mysql-connector-python bcrypt flask-mail

### 4. Création de la base de donnée ###

DROP DATABASE IF EXISTS magasin_informatique;
CREATE DATABASE magasin_informatique;
USE magasin_informatique;

CREATE TABLE clients (
    id INT AUTO_INCREMENT,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL, -- Taille augmentée à 255 pour accueillir les futurs hashs
    adresse VARCHAR(150),
    telephone VARCHAR(20),
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

### 5. Lier l'application à votre BDD ###

db = mysql.connector.connect(
    host="localhost",
    user="VOTRE_UTILISATEUR_MYSQL",  # Exemple: root
    password="VOTRE_MOT_DE_PASSE",
    database="NOM_DE_VOTRE_BDD"
)

### 6. Lancement de l'Application ###

python app.py

### Le terminal affichera que l'application tourne localement. Ouvrez votre navigateur et rendez-vous à l'adresse suivante : ###
👉 http://127.0.0.1:5000