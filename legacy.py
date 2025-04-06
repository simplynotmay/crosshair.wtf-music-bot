

## thnx for using my epic bot

## i am not helping u with it but ifu want some help join the discord server https://crosshair.wtf
## -- u will find it on there soemwhere

## right so hosting:

## u need a lot of cpu ok


## noxia.cloud - i used this


## uh yes!


## enjoy using this bot and scroll down for the code



import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import asyncio
import yt_dlp as youtube_dl
import requests
import json
import os
from datetime import timezone
from datetime import datetime, timedelta


intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix="+", intents=discord.Intents.all()) ## prefix for erm commdn!

voice_clients = {}
song_queue = {}
last_played = {}

  

@client.event
async def on_ready():
    await client.tree.sync()
    server_count = len(client.guilds)
    print(f"Server count: {server_count}")
    await client.change_presence(
        status=discord.Status.idle, 
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=f"{server_count} servers"
        )
    )
## u can make this update regularly i dont care :kek:



@client.tree.command(name="panel", description="Set up the music panel")
async def panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(embed=error_embed("You need ``administrator`` to use this command."), ephemeral=True)
        return

    embed = discord.Embed(
        title="crosshair.wtf Panel",
        description="This is the **crosshair.wtf panel** and can be used to control the bot.",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://crosshair.wtf/icons/panel2.png") ## dont exist no more LEL

    view = MusicPanel(interaction)
    await interaction.response.send_message(embed=embed, view=view)


class MusicPanel(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:play:1345842552971989094>")
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(interaction.guild.id)
        if not vc or not vc.is_connected():
            await interaction.response.send_message(embed=error_embed("You need to make the bot join a Voice Channel."), ephemeral=True)
            return

        if vc.is_paused():
            vc.resume()
        elif song_queue.get(interaction.guild.id):
            await play_next(interaction.guild)
        else:
            await interaction.response.send_message(embed=error_embed("There is no current audio playing."), ephemeral=True)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:pause:1345842590154494106>")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(interaction.guild.id)
        if vc and vc.is_playing():
            vc.pause()
        else:
            await interaction.response.send_message(embed=error_embed("There is no current audio playing."), ephemeral=True)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:skip_previous:1345842488954327062>")
    async def skip_previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.id in last_played:
            song_queue.setdefault(interaction.guild.id, []).insert(0, last_played[interaction.guild.id])
            await play_next(interaction.guild)
        else:
            await interaction.response.send_message(embed=error_embed("There is no song before this!"), ephemeral=True)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:skip_next:1345842522273878046>")
    async def skip_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if song_queue.get(interaction.guild.id):
            await play_next(interaction.guild)
        else:
            await interaction.response.send_message(embed=error_embed("There is no song in the queue!"), ephemeral=True)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:leave_vc:1345842621137813564>")
    async def leave_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = voice_clients.get(interaction.guild.id)
        if vc and vc.is_connected():
            if vc.is_playing():
                await interaction.response.send_message(embed=error_embed("A song is currently playing, you cannot disconnect me at this time!"), ephemeral=True)
            else:
                await vc.disconnect()
        else:
            await interaction.response.send_message(embed=error_embed("I am not currently connected to a VC."), ephemeral=True)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:join_vc:1345863498424385607>")
    async def join_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = VoiceChannelSelect(interaction)
        await interaction.response.send_message("Select a voice channel:", view=view, ephemeral=True)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:link:1345842694181748890>")
    async def link(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = YouTubeURLModal()
        await interaction.response.send_modal(modal)

class YouTubeURLModal(discord.ui.Modal, title="Add YouTube URL"):
    def __init__(self):
        super().__init__()
        self.url = discord.ui.TextInput(
            label="YouTube URL",
            placeholder="Enter the YouTube URL here...",
            required=True,
            max_length=100
        )
        self.add_item(self.url)

    async def on_submit(self, interaction: discord.Interaction):
        url = self.url.value
        guild_id = interaction.guild.id

        if 'list' in url:
            await interaction.response.send_message(embed=error_embed("Sorry, we don't support YouTube playlists. Use our playlist feature here: https://crosshair.wtf/playlists/"), ephemeral=True) ## dont exist no more LEL
            return

        await interaction.response.send_message("<a:LOADING:1348253018554110043> Uploading.... this could take some time.", ephemeral=True)
        song_queue.setdefault(guild_id, []).append(url)
        await interaction.followup.send(embed=success_embed(f"Added to queue: {await get_video_title(url)}"), ephemeral=True)

        vc = voice_clients.get(guild_id)
        if vc and vc.is_connected() and not vc.is_playing():
            await play_next(interaction.guild)

class VoiceChannelSelect(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.interaction = interaction
        voice_channels = interaction.guild.voice_channels
        self.dropdown = VoiceChannelDropdown(voice_channels)
        self.add_item(self.dropdown)

    @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji="<:join_vc:1345863498424385607>")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_channel = self.dropdown.selected_channel
        if not selected_channel:
            await interaction.response.send_message(embed=error_embed("You must select a channel!"), ephemeral=True)
            return
        
        if interaction.guild.id in voice_clients:
            vc = voice_clients[interaction.guild.id]
            if vc.is_connected():
                await interaction.response.send_message(embed=error_embed(f"I am currently in {vc.channel.mention}, use the leave VC button first!"), ephemeral=True)
                return

        vc = await selected_channel.connect()
        voice_clients[interaction.guild.id] = vc
        await interaction.response.edit_message(content=f"Connected to {selected_channel.mention}", view=None)

class VoiceChannelDropdown(discord.ui.Select):
    def __init__(self, voice_channels):
        options = [
            discord.SelectOption(label=vc.name, value=str(vc.id))
            for vc in voice_channels
        ]
        super().__init__(placeholder="Select a Voice Channel", options=options)
        self.selected_channel = None

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        self.selected_channel = discord.utils.get(guild.voice_channels, id=int(self.values[0]))

async def play_next(guild):
    if not song_queue.get(guild.id):
        return
    
    vc = voice_clients.get(guild.id)
    if not vc or not vc.is_connected():
        return
    
    url = song_queue[guild.id].pop(0)
    last_played[guild.id] = url
    
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info["url"]
    
    vc.play(discord.FFmpegPCMAudio(audio_url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild), client.loop))

async def download_playlist(playlist_url):
    response = requests.get(playlist_url)
    links = response.text.splitlines()
    for link in links:
        song_queue.append(link)

async def get_video_title(url):
    with youtube_dl.YoutubeDL({"quiet": True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get("title", "Unknown Title")
        except Exception as e:
            return "Error fetching video title"


@tasks.loop(minutes=1)
async def check_inactivity():
    for guild_id, vc in voice_clients.items():
        if vc.is_connected():
            if len(vc.channel.members) == 1:
                await asyncio.sleep(600)
                if len(vc.channel.members) == 1:
                    await vc.disconnect()
            elif not vc.is_playing():
                await asyncio.sleep(300)
                if not vc.is_playing():
                    for member in vc.channel.members:
                        try:
                            await member.send(embed=disconnect_embed(vc.guild.name))
                        except:
                            pass
                    await vc.disconnect()

def error_embed(message):
    return discord.Embed(title="Error", description=message, color=discord.Color.red())

def success_embed(message):
    return discord.Embed(title="Success", description=message, color=discord.Color.green())

def disconnect_embed(server_name):
    return discord.Embed(title="Bot Disconnected!", description=f"The bot was disconnected from {server_name} due to inactivity.", color=discord.Color.orange())


## you can put ur token here or use .env


client.run("****")
