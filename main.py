import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from deep_translator import GoogleTranslator

app = Flask('')

@app.route('/')
def home():
    return "Bot is on"

def run_flask():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=".", intents=intents)

user_target_lang = {}

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Translator bot {bot.user} is ready!")

@bot.tree.command(name="dich", description="Set your target language for DM")
@app_commands.describe(lang="Language code (eg: en, ja, ko,...)")
async def set_language(interaction: discord.Interaction, lang: str):
    if interaction.guild is not None:
        await interaction.response.send_message("This command can only be used in DMs.", ephemeral=True)
        return
        
    user_target_lang[interaction.user.id] = lang.lower()
    await interaction.response.send_message(f"set target language to {lang.lower()}.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild is not None:
        return

    user_id = message.author.id
    target_lang = user_target_lang.get(user_id, "en")
    
    try:
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(message.content)
        if translated_text and translated_text.strip().lower() != message.content.strip().lower():
            await message.reply(content=translated_text, mention_author=False)
    except Exception as e:
        print(f"Error in DM translate: {e}")

keep_alive()

bot.run(os.getenv("TOKEN"))

