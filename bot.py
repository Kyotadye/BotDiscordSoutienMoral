import os
import random
import re
import string
from datetime import datetime, timedelta
from discord.ext import commands

import discord
import asyncio

TOKEN = 'YOUR_TOKEN'
GUILD_ID = 1178005116914237542

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

channel_info = {}
user_cooldown = {}  # Dictionnaire pour stocker les utilisateurs ayant créé un canal
nombre_pouce_requis = 10
user_states = {}  # Dictionnaire pour suivre l'état des utilisateurs

# Chemin vers le fichier contenant les mots bannis
fichier_mots_bannis = 'mots_bannis.txt'


def log_message(message):
    """
    Log un message dans un fichier texte organisé par date.

    Args:
    message (str): Le message à logger.
    """
    now = datetime.now()
    year_dir = f'logs/{now.year}'
    month_dir = f'{year_dir}/{now.month}'
    log_file = f'{month_dir}/{now.day}.txt'

    # Créer le dossier de l'année si nécessaire
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)

    # Créer le dossier du mois si nécessaire
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)

    # Logger le message dans le fichier du jour
    with open(log_file, 'a') as file:
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - {message}\n")


# Lire les mots bannis à partir du fichier
def lire_mots_bannis():
    """
        Lit les mots bannis à partir d'un fichier texte.
        Retourne une liste des mots bannis.
    """
    try:
        with open(fichier_mots_bannis, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []


# Sauvegarder les mots bannis dans le fichier
def sauvegarder_mots_bannis(banned_words):
    """
        Sauvegarde une liste de mots bannis dans un fichier texte.

        Args:
        banned_words (list): Liste des mots à sauvegarder.
    """
    with open(fichier_mots_bannis, 'w') as file:
        for mot in banned_words:
            file.write(mot + '\n')


@bot.event
async def on_ready():
    """
        Se déclenche lorsque le bot est prêt. Initialise les informations des canaux.
    """
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        guild_id = guild.id
        for channel in guild.text_channels:
            channel_info[(guild_id, channel.name)] = channel.id
        for channel in guild.forums:
            channel_info[(guild_id, channel.name)] = channel.id
    bot.loop.create_task(delete_inactive_channels())


# Fonction pour reconstruire la regex des mots bannis
def reconstruire_regex():
    """
    Reconstruit la regex pour les mots bannis en fonction de la liste actuelle.
    Retourne une regex pour la détection des mots bannis ou None si la liste est vide.
    """
    if mots_bannis != []:
        return r'\b(' + '|'.join(re.escape(mot) for mot in mots_bannis) + r')\b'
    else:
        # Retourne une regex qui ne correspondra à rien si la liste des mots bannis est vide
        return None  # Ceci est une assertion négative qui échouera toujours


@bot.event
async def on_member_join(member):
    """
    Se déclenche lorsqu'un nouveau membre rejoint. Renomme le membre avec un nom aléatoire.

    Args:
    member (discord.Member): Le membre qui a rejoint.
    """
    # Générer une chaîne de caractères aléatoire pour le nouveau nom
    new_name = ''.join(
        random.choices(string.ascii_letters + string.digits, k=10))  # Génère un nom de 10 caractères aléatoires

    try:
        # Renommer le membre avec le nouveau nom
        await member.edit(nick=new_name)
        print(f"Le membre {member.display_name} a été renommé en {new_name}.")
    except discord.Forbidden:
        print(f"Impossible de renommer le membre {member.display_name}. Permission manquante.")


async def delete_inactive_channels():
    """
    Supprime les canaux inactifs sur le serveur. Vérifie périodiquement et supprime les canaux sans activité récente.
    """
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)

    while not bot.is_closed():
        # Récupération du temps actuel moins X jours (temps d'inactivité)
        inactive_time = datetime.utcnow() - timedelta(
            days=7)  # Par exemple, supprimer s'il n'y a pas eu de messages depuis 7 jours

        if guild:
            # Parcours des canaux du serveur
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel) and channel.name == 'discussion-psy':
                    try:
                        # Récupération du dernier message du canal
                        last_message = await channel.fetch_message(
                            channel.last_message_id) if channel.last_message_id else None
                    except discord.NotFound:
                        last_message = None

                    if last_message is None:
                        await channel.delete()
                        print(f"Le canal {channel.name} a été supprimé car il était inactif.")

                    # Comparaison de temps avec le même type (offset-naive)
                    if last_message and last_message.created_at.replace(tzinfo=None) < inactive_time:
                        await channel.delete()
                        print(f"Le canal {channel.name} a été supprimé car il était inactif.")
                pass

            for user_id, last_creation_time in list(user_cooldown.items()):
                # Comparaison avec le temps actuel moins X jours (délai)
                if datetime.utcnow() - last_creation_time >= timedelta(days=7):
                    del user_cooldown[user_id]  # Supprimer l'entrée obsolète

        await asyncio.sleep(7200)  # Vérifier toutes les 2 heures


@bot.event
async def on_message(message):
    """
    Se déclenche à la réception de chaque message. Traite les messages selon leur contenu et le canal.

    Args:
    message (discord.Message): Le message reçu.
    """
    global mots_bannis, regex_mots_bannis, nombre_pouce_requis

    guild = bot.get_guild(GUILD_ID)  # Assurez-vous que GUILD_ID est défini correctement
    user_id = message.author.id

    if user_states.get(user_id) == "attente_titre":
        # Traitez le titre ici
        title_problemes = message.content
        # ... votre logique pour gérer le titre

        # Réinitialisez l'état de l'utilisateur
        user_states[user_id] = None
        return

    member = guild.get_member(message.author.id)
    if not member:
        await message.channel.send("Vous n'êtes pas membre du serveur.")
        return

    if message.author == bot.user:
        return

    if regex_mots_bannis is None:
        contains_banned_word = False
    else:
        contains_banned_word = re.search(regex_mots_bannis, message.content, re.IGNORECASE)

    if contains_banned_word:
        # Traiter le cas où un mot banni est trouvé
        print(f"Message contient un mot banni: {contains_banned_word.group(0)}")
        target_channel_name = "moderation"
        mod_channel_id = channel_info.get(
            (GUILD_ID, target_channel_name))  # Remplace ceci par l'ID du channel de modération
        mod_channel = bot.get_channel(mod_channel_id)
        # Vous pouvez ajouter ici le code pour supprimer le message, avertir l'utilisateur, etc.

        if isinstance(message.channel, discord.TextChannel):
            await message.delete()
            await message.channel.send(
                "Votre message a été supprimé car il contenait un ou plusieurs mots offensants.")
            embed_description = f"Message de **{message.author}** contient " \
                                f"un ou plusieurs mots offensants [id={message.id}] : {message.content}"
            embed = discord.Embed(title="Message non anonmyme anonyme bloqué",
                                  description=embed_description,
                                  color=discord.Color.orange())
            await mod_channel.send(embed=embed)
            log_message(embed_description)
        elif isinstance(message.channel, discord.DMChannel):
            await message.channel.send(
                "Votre message n'a pas été envoyé car il contenait un ou plusieurs mots offensants.")
            embed_description = f"Message de **{message.author}** contient " \
                                f"un ou plusieurs mots offensants [id={message.id}] : {message.content}"
            embed = discord.Embed(title="Message anonyme bloqué",
                                  description=embed_description,
                                  color=discord.Color.orange())
            await mod_channel.send(embed=embed)
            log_message(embed_description)
        return

    if isinstance(message.channel, discord.TextChannel):
        if message.channel.name == 'moderation' and message.content.startswith('!badword'):
            if any(role.name == 'modérateur' for role in message.author.roles):
                parts = message.content.split()
                if len(parts) >= 3:
                    action = parts[1]
                    mot = parts[2]

                    if action == 'add':
                        mots_bannis.append(mot)
                        sauvegarder_mots_bannis(mots_bannis)
                        regex_mots_bannis = reconstruire_regex()
                        await message.channel.send(f"Mot ajouté à la liste des mots bannis: {mot}")

                    elif action == 'delete':
                        if mot in mots_bannis:
                            mots_bannis.remove(mot)
                            sauvegarder_mots_bannis(mots_bannis)
                            regex_mots_bannis = reconstruire_regex()
                            await message.channel.send(f"Mot supprimé de la liste des mots bannis: {mot}")
                        else:
                            await message.channel.send("Ce mot n'est pas dans la liste des mots bannis.")

                    else:
                        await message.channel.send(
                            "Action non reconnue. Utilisez 'add' pour ajouter ou 'delete' pour supprimer.")
                else:
                    await message.channel.send("Usage: !badword [add/delete] [mot]")
            else:
                await message.channel.send("Vous n'avez pas la permission d'utiliser cette commande.")
        elif message.channel.name == 'moderation' and message.content.startswith('!listbadwords'):
            if any(role.name == 'modérateur' for role in message.author.roles):
                await message.channel.send(f"Liste des mots bannis: {', '.join(mots_bannis)}")
        elif message.channel.name == 'moderation' and message.content.startswith('!reportnumber'):
            if any(role.name == 'modérateur' for role in message.author.roles):
                parts = message.content.split()
                if len(parts) >= 2:
                    action = parts[1]
                    if action == 'modify' and len(parts) >= 3:
                        nombre = parts[2]
                        if nombre.isdigit():
                            nombre_pouce_requis = int(nombre)
                            await message.channel.send(f"Nouveau nombre de pouces requis pour qu'un signalement soit "
                                                       f"accepté : {nombre_pouce_requis}")
                        else:
                            await message.channel.send("Le nombre doit être un entier.")
                    elif action == 'check':
                        await message.channel.send(f"Nombre de pouces requis pour qu'un signalement"
                                                   f" soit accepté : {nombre_pouce_requis}")
                    else:
                        await message.channel.send(
                            "Action non reconnue. Utilisez 'modify' pour modifier le nombre de pouces requis ou "
                            "'check' pour vérifier le nombre de pouce requis actuellement.")
        elif message.channel.name == 'moderation' and message.content.startswith('!help'):
            if any(role.name == 'modérateur' for role in message.author.roles):
                embed = discord.Embed(title="Commandes disponibles",
                                      description="**!badword [add/delete] [mot] **: ajoute ou supprime un mot de la "
                                                  "liste des mots bannis \n"
                                                  "**!listbadwords** : liste les mots bannis \n"
                                                  "**!reportnumber [modify/check] [nombre]** : modifie ou affiche le "
                                                  "nombre de pouces requis pour qu'un signalement soit accepté",
                                      color=discord.Color.green())
                await message.channel.send(embed=embed)
            return

    if isinstance(message.channel, discord.DMChannel):
        contains_link = re.search(r'https?://\S+', message.content)  # Vérifie les liens dans le message
        contains_file = len(message.attachments) > 0  # Vérifie s'il y a des pièces jointes dans le message
        # Vérifie la présence de mots bannis

        if contains_link or contains_file:
            await message.channel.send("Le message contient un lien ou un fichier, je ne peux pas le traiter.")
            return

        user_id = message.author.id  # ID de l'utilisateur qui envoie le message privé
        chosen_channel = None  # Canal choisi par l'utilisateur pour envoyer le message
        chose_channel_message = await message.channel.send(
            "Dans quel channel voulez vous envoyer votre message ? Répondez avec les réactions ci-dessous. ("
            "discussions/appel à l'aide/problèmes)(pour un problème décrivez votre problème le titre sera demandé par "
            "la suite)")

        # Ajout des réactions au message pour choisir le canal
        await chose_channel_message.add_reaction("💬")  # Réaction pour envoyer le message dans le canal général
        await chose_channel_message.add_reaction("📢")  # Réaction pour envoyer le message dans le canal appel à l'aide
        await chose_channel_message.add_reaction("❓")  # Réaction pour envoyer le message dans le canal privé

        def check(reaction, user):
            return user.id == user_id and reaction.message.id == chose_channel_message.id

        try:
            reaction, _ = await bot.wait_for('reaction_add', check=check, timeout=60)
        except asyncio.TimeoutError:
            await message.channel.send("Temps écoulé, la confirmation a expiré.")
            return

        problemes = False
        title_problemes = ""
        # Collecter les tags choisis
        chosen_tags = []

        if str(reaction.emoji) == '💬':
            target_channel_name = "discussions"  # Remplace ceci par le nom du canal dans lequel tu veux renvoyer les messages
            # Récupération de l'ID du canal à partir du nom et de l'ID de la guilde
            channel_id = channel_info.get((GUILD_ID, target_channel_name))
        elif str(reaction.emoji) == '📢':
            target_channel_name = "appel-à-laide"  # Remplace ceci par le nom du canal dans lequel tu veux renvoyer les messages
            # Récupération de l'ID du canal à partir du nom et de l'ID de la guilde
            channel_id = channel_info.get((GUILD_ID, target_channel_name))
        elif str(reaction.emoji) == '❓':
            target_channel_name = "problemes"  # Remplace ceci par le nom du canal dans lequel tu veux renvoyer les messages
            # Récupération de l'ID du canal à partir du nom et de l'ID de la guilde
            channel_id = channel_info.get((GUILD_ID, target_channel_name))
            channel = bot.get_channel(channel_id)
            await message.channel.send("Quel est le titre de votre problème ?")
            user_states[user_id] = "attente_titre"
            try:
                title_problemes = await bot.wait_for('message', timeout=60)
            except asyncio.TimeoutError:
                await message.channel.send("Temps écoulé, la confirmation a expiré.")
                user_states[user_id] = ""
                return
            user_states[user_id] = ""
            forum_tags = channel.available_tags
            tag_forum_message = await message.channel.send("Quel tags voulez vous ajouter à votre problème ? Répondez "
                                                           "avec les réactions ci-dessous (ATTENDEZ BIEN QUE TOUTES "
                                                           "APPARAISSENT + PAS PLUS DE 5).\n ({})".format(" / ".join([
                tag.name for tag in forum_tags])))
            await message.channel.send("Si vous avez ajouté tous vos tags réagissez avec ✅")
            list_reactions = ["🩺", "😔", "💑", "🏠", "👨‍💻", "👮", "📱", "⚰️", "🤝", "👥", "🤷", "💰", "👪",
                              "🍆","✅"]
            reaction_to_tag_map = {list_reactions[i]: tag for i, tag in enumerate(forum_tags)}

            for reaction in list_reactions:
                await tag_forum_message.add_reaction(reaction)

            def check3(reaction, user):
                return user.id == user_id and reaction.message.id == tag_forum_message.id and str(
                    reaction) in list_reactions

            while True:
                try:
                    reaction, _ = await bot.wait_for('reaction_add', check=check3, timeout=60)
                    if str(reaction) == "✅":
                        break
                    chosen_tags.append(reaction_to_tag_map[str(reaction)])
                except asyncio.TimeoutError:
                    break

            problemes = True

        else:
            target_channel_name = "discussions"  # Remplace ceci par le nom du canal dans lequel tu veux renvoyer les messages
            # Récupération de l'ID du canal à partir du nom et de l'ID de la guilde
            channel_id = channel_info.get((GUILD_ID, target_channel_name))

        confirmation_message = await message.channel.send(
            "Confirmez vous que vous souhaitez bien envoyer ce message ? Répondez avec les réactions ci-dessous.")

        # Ajout des réactions au message pour confirmer ou annuler
        await confirmation_message.add_reaction("✅")  # Réaction pour confirmer
        await confirmation_message.add_reaction("❌")  # Réaction pour annuler

        def check2(reaction, user):
            return user.id == user_id and reaction.message.id == confirmation_message.id

        try:
            reaction, _ = await bot.wait_for('reaction_add', check=check2, timeout=60)
        except asyncio.TimeoutError:
            await message.channel.send("Temps écoulé, la confirmation a expiré.")
            return

        if str(reaction.emoji) == '✅':
            if message.content.lower() == "je veux un psy":
                # Vérifier si l'utilisateur a déjà créé un canal récemment
                if user_id in user_cooldown and (datetime.utcnow() - user_cooldown[user_id]) < timedelta(days=7):
                    await message.channel.send(
                        "Vous avez déjà créé un canal récemment. Veuillez patienter avant d'en créer un nouveau.")
                    return

                role_name = "Professionnel de sante"
                guild = bot.get_guild(GUILD_ID)
                role = discord.utils.get(guild.roles, name=role_name)

                if role:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        guild.me: discord.PermissionOverwrite(read_messages=True),
                        message.author: discord.PermissionOverwrite(read_messages=True),
                        role: discord.PermissionOverwrite(read_messages=True)
                    }

                    channel = await guild.create_text_channel('discussion-psy', overwrites=overwrites)
                    await channel.send(f"Un canal a été créé pour vous avec le rôle {role_name}.")

                    # Mettre à jour le cooldown de l'utilisateur
                    user_cooldown[user_id] = datetime.utcnow()
            elif problemes:
                name_f = str(title_problemes.content)
                message_f = str(message.content)
                new_thread = await bot.get_channel(channel_id).create_thread(name=name_f,
                                                                             content=message_f,
                                                                             auto_archive_duration=4320,
                                                                             applied_tags=chosen_tags)
            else:
                if channel_id:
                    target_channel = bot.get_channel(channel_id)
                    if target_channel:
                        embed = discord.Embed(
                            title=f"Nouveau message anonyme [id={message.id}]:",
                            description=f"{message.content}",
                            color=discord.Color.blue()  # Vous pouvez choisir la couleur
                        )
                        # await target_channel.send(f"*Nouveau message anonyme [id={message.id}]:*\n{message.content}")
                        await target_channel.send(embed=embed)
                        await message.channel.send("Message envoyé dans le canal spécifique.")
                    else:
                        await message.channel.send(
                            f"Le canal '{target_channel_name}' n'a pas été trouvé sur ce serveur.")
        else:
            await message.channel.send("Opération annulée.")


@bot.event
async def on_reaction_add(reaction, user):
    """
    Se déclenche lorsqu'une réaction est ajoutée à un message. Gère les réactions pour la modération et les fonctionnalités spécifiques.

    Args:
    reaction (discord.Reaction): La réaction ajoutée.
    user (discord.User): L'utilisateur qui a ajouté la réaction.
    """
    global nombre_pouce_requis
    target_channel_name = "moderation"
    mod_channel_id = channel_info.get(
        (GUILD_ID, target_channel_name))  # Remplace ceci par l'ID du channel de modération
    if reaction.emoji == '👎':  # Vérifie la réaction du pouce vers le bas

        if reaction.message.channel.id != mod_channel_id:
            if reaction.count >= nombre_pouce_requis:  # X est le nombre minimum de réactions de pouce vers le bas nécessaire
                content = reaction.message.content
                author_name = reaction.message.author.name

                # Envoie du message copié dans le channel de modération
                mod_channel = bot.get_channel(mod_channel_id)
                if mod_channel:
                    emded_description = f"Message supprimé de {author_name} envoyé à {reaction.message.created_at}:\n{content}"
                    embed = discord.Embed(
                        title=emded_description,
                        description=f"{content}",
                        color=discord.Color.red()  # Vous pouvez choisir la couleur
                    )
                    await mod_channel.send(embed=embed)
                    log_message(emded_description)
                # Suppression du message original
                await reaction.message.delete()


# Liste initiale des mots bannis
mots_bannis = lire_mots_bannis()
regex_mots_bannis = reconstruire_regex()
bot.run(TOKEN)
