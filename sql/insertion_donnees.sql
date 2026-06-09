INSERT INTO clients (nom, prenom, email, password, adresse, telephone) VALUES
('Dupont', 'Marie', 'marie@gmail.com', '1234', 'Paris', '0600000001'),
('Martin', 'Paul', 'paul@gmail.com', '1234', 'Evry', '0600000002'),
('Benali', 'Sofia', 'sofia@gmail.com', '1234', 'Corbeil', '0600000003');

INSERT INTO produits (nom, description, prix, stock, image) VALUES
('Ordinateur portable HP', 'PC portable 15 pouces', 699.99, 10, 'hp.jpg'),
('Souris Logitech', 'Souris sans fil', 19.99, 50, 'souris.jpg'),
('Clavier Gamer', 'Clavier RGB mécanique', 49.99, 25, 'clavier.jpg'),
('Écran Samsung', 'Écran 24 pouces Full HD', 129.99, 15, 'ecran.jpg');
INSERT INTO commandes (id_client, date_commande, total, statut) VALUES
(1, '2026-06-01', 719.98, 'En attente'),
(2, '2026-06-01', 49.99, 'Validée');