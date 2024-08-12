import discord
from discord.ext import commands
import sqlite3
from datetime import datetime

# Hier sind die verbotenen Wörter, die der Bot überwachen soll.
FORBIDDEN_WORDS = ['verboteneswort1', 'verboteneswort2', 'beleidigung1']

# Erstelle eine Instanz des Bots
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Verbindung zur SQLite-Datenbank herstellen (oder erstellen, falls sie nicht existiert)
conn = sqlite3.connect('ban_database.db')
c = conn.cursor()

# Tabelle für gebannte Benutzer erstellen (falls nicht vorhanden)
c.execute('''CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                banned_at TEXT,
                reason TEXT
            )''')
conn.commit()

@bot.event
async def on_ready():
    print(f'Wir haben uns als {bot.user} eingeloggt')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Überprüfen, ob eine Nachricht verbotene Wörter enthält
    if any(word in message.content.lower() for word in FORBIDDEN_WORDS):
        await message.delete()
        await message.channel.send(f'{message.author.mention}, dein Beitrag wurde entfernt wegen verbotener Wörter.')

        # Aktion abhängig von der Schwere des Vergehens
        if any(word in message.content.lower() for word in FORBIDDEN_WORDS[:1]):  # Zeitüberschreitung
            await message.author.timeout_for(600)  # Timeout für 10 Minuten
            await message.channel.send(f'{message.author.mention} wurde für 10 Minuten getimeoutet.')
        elif any(word in message.content.lower() for word in FORBIDDEN_WORDS[1:2]):  # Kick
            await message.author.kick(reason="Verwenden verbotener Wörter")
            await message.channel.send(f'{message.author.mention} wurde vom Server gekickt.')
        else:  # Bann
            await message.author.ban(reason="Ernst gemeinte Beleidigung oder mehrfaches Vergehen")
            await message.channel.send(f'{message.author.mention} wurde vom Server gebannt.')
            ban_user_across_servers(message.author)

    # Überprüfen auf Spam von Links
    if "http" in message.content or "www" in message.content:
        await message.delete()
        await message.channel.send(f'{message.author.mention}, das Posten von Links ist nicht erlaubt.')

    await bot.process_commands(message)

def ban_user_across_servers(user):
    """Synchronisiert den Bann des Benutzers auf allen verbundenen Servern."""
    for guild in bot.guilds:
        member = guild.get_member(user.id)
        if member:
            c.execute("INSERT INTO bans (user_id, username, banned_at, reason) VALUES (?, ?, ?, ?)", 
                      (user.id, str(user), datetime.utcnow().isoformat(), "Synchronisierter Bann"))
            conn.commit()
            await guild.ban(user, reason="Synchronisierter Bann")

@bot.command()
@commands.has_permissions(ban_members=True)
async def syncban(ctx, user: discord.User, *, reason=None):
    """Manueller Befehl, um Benutzer über alle Server hinweg zu bannen."""
    ban_user_across_servers(user)
    await ctx.send(f'{user.name} wurde auf allen verbundenen Servern gebannt.')

@bot.command()
@commands.has_permissions(ban_members=True)
async def syncunban(ctx, user: discord.User):
    """Manueller Befehl, um Benutzer auf allen Servern zu entbannen."""
    for guild in bot.guilds:
        member = guild.get_member(user.id)
        if member:
            await guild.unban(user)
            await ctx.send(f'{user.name} wurde auf allen verbundenen Servern entbannt.')

# Starte den Bot
bot.run('DEIN_BOT_TOKEN')
Erklärung des Codes:
Verbotene Wörter und Aktionen:

Der Bot überprüft Nachrichten auf das Vorkommen verbotener Wörter. Je nach dem Wort, das gefunden wird, wird der Benutzer entweder in den Timeout versetzt, gekickt oder gebannt.
Link-Spam:

Nachrichten, die Links enthalten, werden automatisch gelöscht, und der Benutzer wird darauf hingewiesen.
Synchronisierung der Bans:

Wenn ein Benutzer auf einem Server gebannt wird, wird der Bann automatisch auf allen Servern, auf denen der Bot aktiv ist, synchronisiert.
Manuelle Synchronisierungsbefehle:

Admins können den Befehl !syncban @Benutzer verwenden, um einen Benutzer manuell über alle Server hinweg zu bannen, und !syncunban @Benutzer, um einen Benutzer zu entbannen.
Schritt 3: Umgebungsvariablen setzen und den Bot starten
Discord-Bot-Token: Setze den DISCORD_TOKEN Umgebungsvariablenwert in Railway oder in deiner Entwicklungsumgebung.
Bot starten: Starte den Bot, indem du das bot.py Skript ausführst.
Schritt 4: Bot auf mehreren Servern hinzufügen
Hinzufügen des Bots zu weiteren Servern:
Gehe zum Discord Developer Portal und erzeuge eine Bot-Einladungs-URL. Verwende die URL, um den Bot zu den Servern hinzuzufügen, auf denen du die Bann-Synchronisierung aktivieren möchtest.
Wichtige Hinweise:
Datenbank: Der Code verwendet eine SQLite-Datenbank, um Banninformationen zu speichern. Du kannst die Datenbank anpassen oder erweitern, um zusätzliche Informationen zu speichern.
Feinabstimmung: Passe die Liste der verbotenen Wörter und die entsprechende Aktion (Timeout, Kick, Bann) an deine Anforderungen an.
Erweiterbarkeit: Der Bot kann weiterentwickelt werden, um spezifischere Regeln und Aktionen zu unterstützen.
Dieser Bot sollte dir eine solide Grundlage geben, um Benutzer automatisch zu moderieren und Banns über mehrere Server zu synchronisieren. Wenn du Fragen hast oder Hilfe bei der Anpassung des Bots benötigst, stehe ich dir gerne zur Verfügung!




Bei folgenden Wörtern folgt ein Timeout für 24h
Hurensohn, Hundesohn, Noob Server
Wenn ein User 5x versucht hat einen unberechtigten Link zu senden, wird er für immer gebannt.
Der bot wird: Clemens's Bann Bot heißen
Berücksichtige dies alles und schreibe mir den fertigen code

Hier ist der angepasste Code für deinen Discord-Bot "Clemens's Bann Bot", der die von dir gewünschten Anforderungen erfüllt:

Schritt 1: Erstelle den bot.py-Code
python
Code kopieren
import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta

# Verbotene Wörter für 24h Timeout
FORBIDDEN_WORDS_TIMEOUT = ['hurensohn', 'hundesohn', 'noob server']

# Dictionary zur Nachverfolgung von Link-Spam-Versuchen
link_attempts = {}

# Erstelle eine Instanz des Bots
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, description="Clemens's Bann Bot")

# Verbindung zur SQLite-Datenbank herstellen (oder erstellen, falls sie nicht existiert)
conn = sqlite3.connect('ban_database.db')
c = conn.cursor()

# Tabelle für gebannte Benutzer erstellen (falls nicht vorhanden)
c.execute('''CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                banned_at TEXT,
                reason TEXT
            )''')
conn.commit()

@bot.event
async def on_ready():
    print(f'Wir haben uns als {bot.user} eingeloggt')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Überprüfen, ob eine Nachricht verbotene Wörter für 24h Timeout enthält
    if any(word in message.content.lower() for word in FORBIDDEN_WORDS_TIMEOUT):
        await message.delete()
        await message.channel.send(f'{message.author.mention}, deine Nachricht enthält verbotene Wörter und du wurdest für 24 Stunden gesperrt.')
        await message.author.timeout_for(timedelta(hours=24))
        return

    # Überprüfen auf Spam von Links
    if "http" in message.content or "www" in message.content:
        await message.delete()
        user_id = message.author.id
        link_attempts[user_id] = link_attempts.get(user_id, 0) + 1

        if link_attempts[user_id] >= 5:
            await message.author.ban(reason="Wiederholter unberechtigter Link-Spam")
            await message.channel.send(f'{message.author.mention} wurde für wiederholten Link-Spam permanent gebannt.')
            ban_user_across_servers(message.author)
        else:
            await message.channel.send(f'{message.author.mention}, das Posten von Links ist nicht erlaubt. Versuch {link_attempts[user_id]} von 5.')

    await bot.process_commands(message)

async def ban_user_across_servers(user):
    """Synchronisiert den Bann des Benutzers auf allen verbundenen Servern."""
    for guild in bot.guilds:
        member = guild.get_member(user.id)
        if member:
            c.execute("INSERT INTO bans (user_id, username, banned_at, reason) VALUES (?, ?, ?, ?)", 
                      (user.id, str(user), datetime.utcnow().isoformat(), "Synchronisierter Bann wegen Link-Spam"))
            conn.commit()
            await guild.ban(user, reason="Synchronisierter Bann wegen Link-Spam")

@bot.command()
@commands.has_permissions(ban_members=True)
async def syncban(ctx, user: discord.User, *, reason=None):
    """Manueller Befehl, um Benutzer über alle Server hinweg zu bannen."""
    await ban_user_across_servers(user)
    await ctx.send(f'{user.name} wurde auf allen verbundenen Servern gebannt.')

@bot.command()
@commands.has_permissions(ban_members=True)
async def syncunban(ctx, user: discord.User):
    """Manueller Befehl, um Benutzer auf allen Servern zu entbannen."""
    for guild in bot.guilds:
        member = guild.get_member(user.id)
        if member:
            await guild.unban(user)
            await ctx.send(f'{user.name} wurde auf allen verbundenen Servern entbannt.')

# Starte den Bot
bot.run('DEIN_BOT_TOKEN')
