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
