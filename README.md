# Bot Discord pour la Modération et la Communication Anonyme

Ce bot Discord est conçu pour améliorer la modération et permettre la communication anonyme au sein des serveurs Discord. Il offre des fonctionnalités telles que la suppression automatique de messages, la gestion de mots bannis, et la possibilité pour les utilisateurs d'envoyer des messages anonymes via le bot.

## Fonctionnalités

- **Suppression Automatique des Messages Inactifs :** Supprime automatiquement les messages des canaux inactifs après une période spécifiée.
- **Gestion des Mots Bannis :** Permet aux modérateurs de gérer une liste de mots bannis. Les messages contenant ces mots sont automatiquement supprimés ou signalés.
- **Renommage Automatique des Nouveaux Membres :** Attribue un nom aléatoire aux nouveaux membres pour maintenir l'anonymat.
- **Communication Anonyme :** Les utilisateurs peuvent envoyer des messages anonymes à des canaux spécifiques via des messages privés au bot.
- **Modération Réactive :** Les utilisateurs peuvent réagir à des messages pour signaler un contenu inapproprié.

## Prérequis

- Python 3.8 ou supérieur
- Bibliothèque discord.py
- Un token de bot Discord valide

## Installation

1. **Installer Python :** Assurez-vous d'avoir Python 3.8 ou supérieur installé sur votre système.
2. **Installer discord.py :** Exécutez `pip install discord.py` pour installer la bibliothèque nécessaire.
3. **Configurer le Token :** Obtenez un token de bot depuis le [Portail des Développeurs Discord](https://discord.com/developers/applications) et remplacez `YOUR_BOT_TOKEN_HERE` dans le script par votre token de bot.

## Configuration

- **Paramétrer les ID de Serveur :** Configurez `GUILD_ID` avec l'ID de votre serveur Discord.
- **Configurer les Canaux :** Assurez-vous que les noms des canaux dans le script correspondent à ceux de votre serveur.

## Utilisation

1. **Démarrer le Bot :** Exécutez le script Python pour démarrer le bot.
2. **Modération :** Utilisez les commandes de modération (`!badword`, `!listbadwords`, `!reportnumber`) dans le canal de modération.
3. **Messages Anonymes :** Les utilisateurs peuvent envoyer des messages privés au bot pour les rediriger anonymement vers un canal spécifié.

## Contribution

Les contributions à ce projet sont les bienvenues. Si vous avez des suggestions ou des améliorations, n'hésitez pas à créer une pull request ou un issue sur le dépôt GitHub du projet.



PS : Je n'ai même pas lu le readme c'est chat gpt qui me l'a fait ^^
