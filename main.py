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
    return "Bot is alive"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=".", intents=intents)

user_target_lang = {}

def bot_response(user_id, text):
    target_lang = user_target_lang.get(user_id, "en")
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except:
        return text

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Translator bot {bot.user} is ready!")

@bot.tree.command(name="setdich", description="Set your target language")
@app_commands.describe(lang="Language code (eg: en, ja, ko)")
async def set_language(interaction: discord.Interaction, lang: str):
    user_id = interaction.user.id
    user_target_lang[user_id] = lang.lower()
    
    success_msg = bot_response(user_id, f"set target language to {lang.lower()}.")
    await interaction.response.send_message(success_msg)

@bot.tree.command(name="dich", description="enter the message you want to translate")
@app_commands.describe(message="the message you want translated")
async def server_translate(interaction: discord.Interaction, message: str):
    user_id = interaction.user.id
    target_lang = user_target_lang.get(user_id, "en")

    if not message or not message.strip():
        msg = bot_response(user_id, "erro: Empty message")
        await interaction.response.send_message(msg)
        return

    try:
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(message)
        await interaction.response.send_message(translated_text)
    except Exception as e:
        msg = bot_response(user_id, f"erro: {e}")
        await interaction.response.send_message(msg)

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

bot.run(os.getenv("DISCORD_TOKEN"))
