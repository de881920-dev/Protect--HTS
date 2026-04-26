import discord
from discord.ext import commands
import asyncio
import random
import os
from dotenv import load_dotenv

# Charge les variables d'environnement (pour Railway)
load_dotenv()

# --- CONFIGURATION DES IDS ---
ROLE_MOD_TICKET = 1426124085015871519
ROLE_BOUTIQUE = 1426124084194054247
ROLE_MOD_GENERAL = 1426124031660392480 

CATEGORIES = {
    "RECRUTEMENT": 1471952984584749220,
    "HTS SHOP": 1426124241136259102,
    "COMMUNITY MANAGER": 1426124242793009235,
    "QUESTION": 1426124243682332699,
    "PARTENARIAT": 1426124245318242306,
    "STAFF": 1426124247553544263,
    "AUTRE": 1426124248455446530
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# --- SYSTÈME DE TICKETS ---
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="HTS SHOP", emoji="🛒", description="Achats Boutique"),
            discord.SelectOption(label="RECRUTEMENT", emoji="📝"),
            discord.SelectOption(label="COMMUNITY MANAGER", emoji="📱"),
            discord.SelectOption(label="QUESTION", emoji="❓"),
            discord.SelectOption(label="PARTENARIAT", emoji="🤝"),
            discord.SelectOption(label="STAFF", emoji="🛡️"),
            discord.SelectOption(label="AUTRE", emoji="⚙️"),
        ]
        super().__init__(placeholder="Choisissez une raison pour ouvrir un ticket...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        choix = self.values[0]
        guild = interaction.guild
        role_to_ping = ROLE_BOUTIQUE if choix == "HTS SHOP" else ROLE_MOD_TICKET
        category_id = CATEGORIES.get(choix)
        category = guild.get_channel(category_id)

        if category is None:
            return await interaction.followup.send(f"❌ Erreur : Catégorie `{choix}` introuvable.", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(role_to_ping): discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        try:
            channel = await guild.create_text_channel(
                name=f"{choix.lower().replace(' ', '-')}-{interaction.user.name}", 
                overwrites=overwrites,
                category=category
            )
            await interaction.followup.send(f"✅ Ticket créé : {channel.mention}", ephemeral=True)
            
            embed = discord.Embed(
                title=f"Ticket - {choix}",
                description=f"Bienvenue {interaction.user.mention},\nLe staff <@&{role_to_ping}> va vous répondre.\n\nUtilisez `!close` pour fermer.",
                color=0x2b2d31
            )
            await channel.send(content=f"{interaction.user.mention} | <@&{role_to_ping}>", embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur : {e}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(
        title="Système de Ticket", 
        description="Choisissez la catégorie ci-dessous pour ouvrir un ticket.", 
        color=0x2b2d31
    )
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def close(ctx):
    valid_categories = [c.lower().replace(" ", "-") for c in CATEGORIES.keys()]
    if any(word in ctx.channel.name for word in valid_categories):
        await ctx.send("🗑️ **Fermeture du ticket dans 5 secondes...**")
        await asyncio.sleep(5)
        await ctx.channel.delete()

# --- GIVEAWAY ---
class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="0", style=discord.ButtonStyle.secondary, custom_id="giveaway_btn")
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.participants:
            self.participants.append(interaction.user.id)
            button.label = str(len(self.participants))
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("Tu participes déjà !", ephemeral=True)

@bot.command()
@commands.has_role(ROLE_MOD_GENERAL)
async def gstart(ctx, temps: int, winners: int, emoji: str, *, lot: str):
    embed = discord.Embed(
        title=f"Giveaway: {lot}",
        description=f"Cliquez sur le bouton {emoji} pour participer\n**Gagnants:** {winners}\nFin dans {temps} min.",
        color=0xf47fff
    )
    view = GiveawayView()
    view.children[0].emoji = emoji
    await ctx.send(embed=embed, view=view)
    await asyncio.sleep(temps * 60)

    if not view.participants:
        return await ctx.send(f"Aucun participant pour : **{lot}**.")

    gagnants = random.sample(view.participants, min(len(view.participants), winners))
    mentions = ", ".join([f"<@{uid}>" for uid in gagnants])
    await ctx.send(f"🎉 Félicitations {mentions} ! Vous gagnez : **{lot}** !")

# --- MODERATION ---
@bot.command()
@commands.has_role(ROLE_MOD_GENERAL)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)

@bot.command()
@commands.has_role(ROLE_MOD_GENERAL)
async def ban(ctx, member: discord.Member, *, reason="Aucune raison"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} a été banni.")

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user.name}")

# Lancement avec le token Railway
bot.run(os.getenv("TOKEN"))
