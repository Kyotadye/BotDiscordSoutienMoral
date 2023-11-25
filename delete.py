import discord
import asyncio
from datetime import datetime, timedelta

TOKEN = "YOUR_BOT_TOKEN_HERE"
GUILD_ID = 1178005116914237542

client = discord.Client(intents=discord.Intents.all())

channel_info = {}


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    for guild in client.guilds:
        guild_id = guild.id
        for channel in guild.text_channels:
            channel_info[(guild_id, channel.name)] = channel.id
    client.loop.create_task(daily_check())


async def delete_old_messages():
    # Ton canal spécifique où tu veux supprimer les messages
    target_channel_name = "moderation"
    mod_channel_id = channel_info.get(
        (GUILD_ID, target_channel_name))  # Remplace ceci par l'ID du channel de modération
    target_channel_name = "discussion-psy"
    discussion_psy_channel_id = channel_info.get(
        (GUILD_ID, target_channel_name))  # Remplace ceci par l'ID du channel de modération
    guild = client.get_guild(GUILD_ID)
    for channel in guild.text_channels:
        if channel.id != mod_channel_id and channel.id != discussion_psy_channel_id:
            # Récupère la date actuelle moins deux semaines
            limit_date = datetime.utcnow() - timedelta(weeks=4)

            async for message in channel.history(limit=None, oldest_first=True):
                if message.created_at.replace(tzinfo=None) < limit_date.replace(tzinfo=None):
                    await message.delete()
                    print(f"Message supprimé : {message.content}")


async def daily_check():
    while True:
        await delete_old_messages()  # Appelle la fonction pour supprimer les messages vieux de plus de deux semaines
        await asyncio.sleep(86400)  # Attend une journée (24 heures) avant de vérifier à nouveau


client.run(TOKEN)
