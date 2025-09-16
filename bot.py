import os
import secrets
import string
import discord
import aiohttp
import aiosqlite
import hashlib
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")

PTERO_URL = os.getenv("PTERO_URL")  # e.g. https://gp.loftix.host
PTERO_API_KEY = os.getenv("PTERO_API_KEY")
NODE_ID = int(os.getenv("PTERO_NODE_ID"))
EGG_ID = int(os.getenv("PTERO_EGG_ID"))
DOCKER_IMAGE = os.getenv("PTERO_IMAGE")
MAX_SERVERS_PER_NODE = int(os.getenv("MAX_SERVERS_PER_NODE", 100))  # default 50 if not set

DATABASE = "botdata.db"
PANEL_LINK = os.getenv("PANEL_LINK", "https://gp.loftix.host/")

intents = discord.Intents.default()
intents.guilds = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents, application_id=int(APPLICATION_ID))


# ---------- Helpers ----------
def gen_password(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def db_init():
    async with aiosqlite.connect(DATABASE) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            email TEXT,
            ptero_user_id INTEGER,
            password_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS servers (
            discord_id TEXT PRIMARY KEY,
            server_id TEXT
        );
        """)
        await db.commit()


async def ptero_request(method, endpoint, json=None):
    headers = {
        "Authorization": f"Bearer {PTERO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"{PTERO_URL.rstrip('/')}/api/application{endpoint}"
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=json) as resp:
            try:
                data = await resp.json(content_type=None)
            except:
                data = await resp.text()
            if resp.status not in (200, 201):
                raise Exception(f"Pterodactyl API error {resp.status}: {data}")
            return data


# ---------- Commands ----------
@bot.tree.command(name="register", description="Register with email (only once)")
@app_commands.describe(email="Your email address")
@app_commands.checks.cooldown(1, 1.0)  # limit: 1 use per 1s
async def register(interaction: discord.Interaction, email: str):
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    # check if already registered
    async with aiosqlite.connect(DATABASE) as db:
        cur = await db.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        if await cur.fetchone():
            await interaction.followup.send("❌ You are already registered.", ephemeral=True)
            return

    password = gen_password()
    password_hash = hash_password(password)

    # Create user on Pterodactyl
    payload = {
        "email": email,
        "username": f"user_{discord_id}",
        "first_name": interaction.user.name,
        "last_name": "Discord",
        "password": password
    }
    try:
        user = await ptero_request("POST", "/users", payload)
        user_id = user["attributes"]["id"]
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to create user: {e}", ephemeral=True)
        return

    # Save locally
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (discord_id, email, user_id, password_hash))
        await db.commit()

    try:
        await interaction.user.send(
            f"✅ Registered!\n"
            f"Panel: {PANEL_LINK}\n"
            f"Email: `{email}`\n"
            f"Password: `{password}`"
        )
        await interaction.followup.send("I sent your login credentials via DM.", ephemeral=True)
    except:
        await interaction.followup.send("✅ Registered, but I couldn’t DM you. Open your DMs!", ephemeral=True)


@bot.tree.command(name="create_free", description="Create your free Minecraft server (1 per user)")
@app_commands.checks.cooldown(1, 1.0)  # limit: 1 use per 1s
async def create_free(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    discord_id = str(interaction.user.id)

    # check if registered
    async with aiosqlite.connect(DATABASE) as db:
        cur = await db.execute("SELECT ptero_user_id FROM users WHERE discord_id = ?", (discord_id,))
        row = await cur.fetchone()
        if not row:
            await interaction.followup.send("❌ You need to register first with `/register`.", ephemeral=True)
            return
        ptero_user_id = row[0]

        # check if server already exists
        cur = await db.execute("SELECT * FROM servers WHERE discord_id = ?", (discord_id,))
        if await cur.fetchone():
            await interaction.followup.send("❌ You already have a server.", ephemeral=True)
            return

    # ✅ Check node server limit
    try:
        all_servers = await ptero_request("GET", "/servers")
        current_servers = sum(1 for s in all_servers["data"] if s["attributes"]["node"] == NODE_ID)
        if current_servers >= MAX_SERVERS_PER_NODE:
            await interaction.followup.send("❌ Server limit reached on this node. Please try again later.", ephemeral=True)
            return
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to check node limit: {e}", ephemeral=True)
        return

    # ✅ Get a free allocation automatically
    try:
        allocs = await ptero_request("GET", f"/nodes/{NODE_ID}/allocations")
        free_alloc = next(
            (a for a in allocs["data"] if not a["attributes"]["assigned"]),
            None
        )
        if not free_alloc:
            await interaction.followup.send("❌ No free allocations available on this node.", ephemeral=True)
            return
        alloc_id = free_alloc["attributes"]["id"]
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to get allocations: {e}", ephemeral=True)
        return

    # ✅ Create server on Pterodactyl
    server_name = interaction.user.name[:20]  # keep under 20 chars (panel limit)

    payload = {
        "name": server_name,
        "user": ptero_user_id,
        "egg": EGG_ID,
        "docker_image": DOCKER_IMAGE,
        "startup": "java -Xms512M -Xmx1G -XX:+UseG1GC -XX:+DisableExplicitGC -jar minecraft_server.jar nogui",
        "limits": {
            "memory": 6144,
            "swap": 0,
            "disk": 20480,
            "io": 500,
            "cpu": 150
        },
        "environment": {
            "SERVER_JARFILE": "minecraft_server.jar",
            "VERSION": "latest",
            "BUILD_NUMBER": "latest"
        },
        "allocation": {
            "default": alloc_id
        },
        "feature_limits": {
            "databases": 1,
            "allocations": 1,
            "backups": 1
        }
    }

    try:
        server = await ptero_request("POST", "/servers", payload)
        server_id = server["attributes"]["id"]
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to create server: {e}", ephemeral=True)
        return

    # Save locally
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("INSERT INTO servers VALUES (?, ?)", (discord_id, server_id))
        await db.commit()

    try:
        await interaction.user.send(
            f"✅ Your free server has been created!\n"
            f"Panel: {PANEL_LINK}\n"
            f"Server ID: `{server_id}`"
        )
        await interaction.followup.send("Server created! Check your DMs.", ephemeral=True)
    except:
        await interaction.followup.send("Server created, but I couldn’t DM you. Open your DMs!", ephemeral=True)


# ---------- Error handler for cooldown ----------
@register.error
@create_free.error
async def cooldown_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Please wait {error.retry_after:.1f}s before using this command again.",
            ephemeral=True
        )


# ---------- Startup ----------
@bot.event
async def on_ready():
    await db_init()
    await bot.tree.sync()
    print(f"Bot is ready as {bot.user}")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
