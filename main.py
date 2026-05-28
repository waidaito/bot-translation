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
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=".", intents=intents)

user_target_lang = {}

class LanguageSelect(discord.ui.Select):
    def __init__(self, foreign_text):
        self.foreign_text = foreign_text
        options = [
            discord.SelectOption(label="Tiếng Việt", value="vi"),
            discord.SelectOption(label="Tiếng Anh", value="en"),
            discord.SelectOption(label="Tiếng Nhật", value="ja"),
            discord.SelectOption(label="Tiếng Hàn", value="ko"),
            discord.SelectOption(label="Tiếng Trung", value="zh-cn")
        ]
        super().__init__(placeholder="Chọn ngôn ngữ muốn dịch...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_lang = self.values[0]
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(self.foreign_text)
            await interaction.followup.send(content=translated_text, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(content=f"erro: {e}", ephemeral=True)

class LanguageView(discord.ui.View):
    def __init__(self, foreign_text):
        super().__init__(timeout=60)
        self.add_item(LanguageSelect(foreign_text))

@bot.event
async def on_ready():
    try:
        bot.tree.add_command(ctx_menu_translate)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Translator bot {bot.user} is ready!")

@bot.tree.command(name="setdich", description="Set your target language for DM")
@app_commands.describe(lang="Language code (eg: en, ja, ko)")
@app_commands.dm_only()
async def set_language(interaction: discord.Interaction, lang: str):
    user_target_lang[interaction.user.id] = lang.lower()
    await interaction.response.send_message(f"set target language to {lang.lower()}.", ephemeral=True)

@app_commands.context_menu(name="dich")
async def ctx_menu_translate(interaction: discord.Interaction, message: discord.Message):
    if interaction.guild is None:
        await interaction.response.send_message("Lệnh này chỉ dùng ở Server thường.", ephemeral=True)
        return

    foreign_text = message.content
    if not foreign_text or not foreign_text.strip():
        await interaction.response.send_message("erro: Tin nhắn trống", ephemeral=True)
        return

    view = LanguageView(foreign_text)
    await interaction.response.send_message("Chọn ngôn ngữ bro muốn dịch sang bên dưới:", view=view, ephemeral=True)

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
