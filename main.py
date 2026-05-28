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

class LanguageSelect(discord.ui.Select):
    def __init__(self, foreign_text, user_id):
        self.foreign_text = foreign_text
        self.user_id = user_id
        
        target_lang = user_target_lang.get(user_id, "en")
        placeholder_text = GoogleTranslator(source='auto', target=target_lang).translate("Choose a language to translate...")
        
        options = [
            discord.SelectOption(label="Tiếng Việt", value="vi"),
            discord.SelectOption(label="Tiếng Anh", value="en"),
            discord.SelectOption(label="Tiếng Nhật", value="ja"),
            discord.SelectOption(label="Tiếng Hàn", value="ko"),
            discord.SelectOption(label="Tiếng Trung", value="zh-cn")
        ]
        super().__init__(placeholder=placeholder_text, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            target_lang = self.values[0]
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(self.foreign_text)
            await interaction.followup.send(content=translated_text)
        except Exception as e:
            msg = bot_response(self.user_id, f"erro: {e}")
            await interaction.followup.send(content=msg)

class LanguageView(discord.ui.View):
    def __init__(self, foreign_text, user_id):
        super().__init__(timeout=60)
        self.add_item(LanguageSelect(foreign_text, user_id))

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Translator bot {bot.user} is ready!")

@bot.tree.command(name="setdich", description="Set your target language for DM")
@app_commands.describe(lang="Language code (eg: en, ja, ko)")
@app_commands.dm_only()
async def set_language(interaction: discord.Interaction, lang: str):
    user_id = interaction.user.id
    user_target_lang[user_id] = lang.lower()
    
    success_msg = bot_response(user_id, f"set target language to {lang.lower()}.")
    await interaction.response.send_message(success_msg)

@bot.tree.command(name="dich", description="Dịch tin nhắn nhập vào")
@app_commands.describe(message="Tin nhắn bro muốn dịch")
async def server_translate(interaction: discord.Interaction, message: str):
    user_id = interaction.user.id

    if interaction.guild is None:
        msg = bot_response(user_id, "This command can only be used in servers.")
        await interaction.response.send_message(msg)
        return

    if not message or not message.strip():
        msg = bot_response(user_id, "erro: Empty message")
        await interaction.response.send_message(msg)
        return

    view = LanguageView(message, user_id)
    title_msg = bot_response(user_id, f"Choose a language to translate this message:")
    await interaction.response.send_message(f"{title_msg} *\"{message}\"*", view=view)

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
