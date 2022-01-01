import json
import random
import discord
from discord.ext import tasks
import requests
import datetime
import os
from dotenv import load_dotenv
import random

load_dotenv()

LIST_OF_FRIENDS = ["SaltySandyHS", "alostaz47", "The Number 3", "ExistToCease", "gura tft player", "gamesuxbtw"]
FRIENDS_LAST_GAME_PLAYED = {"SaltySandyHS":None, "alostaz47":None, "The Number 3":None, "ExistToCease":None, "gura tft player":None, "gamesuxbtw":None}
FLAME_MESSAGE_1 = "Hey what happened :slight_smile:"
FLAME_MESSAGE_2 = ":slight_smile:"
FLAME_MESSAGE_3 = "It clicked btw"
FLAME_MESSAGE_4 = ":clown:"
FLAME_MESSAGE_5 = "It's just a warmup game"
FLAME_MESSAGE_LIST = [FLAME_MESSAGE_1, FLAME_MESSAGE_2, FLAME_MESSAGE_3, FLAME_MESSAGE_4, FLAME_MESSAGE_5]

headers = {"X-Riot-Token": os.environ.get("RIOT_API_TOKEN")}

client = discord.Client()

def get_timedelta(match_id):
    response_recent_match = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/" + match_id, headers=headers).content.decode())

    timedelta = datetime.datetime.now() - datetime.datetime.fromtimestamp(response_recent_match['info']['game_datetime'] / 1e3)

    return timedelta.seconds

def get_last_ranking(summoner_name):

    response_ids = json.loads(requests.get("https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/" + summoner_name, headers=headers).content.decode())
    response_matches = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/" + response_ids['puuid'] + "/ids?count=1", headers=headers).content.decode())
    response_recent_match = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/" + response_matches[0], headers=headers).content.decode())

    rank = -1

    for player in response_recent_match['info']['participants']:
        if player['puuid'] == response_ids['puuid']:
            rank = player['placement']

    if rank > 4:
        return True
    return False

def get_most_recent_match(summoner_name):

    response_ids = json.loads(requests.get("https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/" + summoner_name, headers=headers).content.decode())

    response_matches = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/" + response_ids['puuid'] + "/ids?count=1", headers=headers).content.decode())
    return response_matches[0]

def get_data_for_user(summoner_name):

    strings = []

    response_ids = json.loads(requests.get("https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/" + summoner_name, headers=headers).content.decode())
    response_rank = json.loads(requests.get("https://na1.api.riotgames.com/tft/league/v1/entries/by-summoner/" + response_ids["id"], headers=headers).content.decode())[0]
    strings.append(summoner_name + " is currently " + response_rank['tier'] + " " + response_rank['rank'] + ", " + str(response_rank['leaguePoints']) + " LP.")

    response_matches = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/" + response_ids['puuid'] + "/ids?count=1", headers=headers).content.decode())

    response_recent_match = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/" + response_matches[0], headers=headers).content.decode())

    timedelta = datetime.datetime.now() - datetime.datetime.fromtimestamp(response_recent_match['info']['game_datetime'] / 1e3)
    hours = timedelta.seconds//3600
    minutes = timedelta.seconds//60 - hours * 60
    seconds = timedelta.seconds - hours * 3600 - minutes * 60

    rank = -1

    for player in response_recent_match['info']['participants']:
        if player['puuid'] == response_ids['puuid']:
            rank = player['placement']

    strings.append(str(timedelta.days) + " days, " + str(hours) + " hours, " + str(minutes) + " minutes, " + str(seconds) + " seconds ago, " + summoner_name + " finished " + str(rank) + "/8.")
    return strings

list_of_hani_insults = ["Hey what happened :slight_smile:", ":clown:", "sine waving i see you", "heyyy hani are you lowering your mmr for easier lobbies?"]

list_of_sandy_insults = ["imagine being lapped by hani", "dude clean your room instead of playing"]
@client.event
async def on_message(message):
    if message.content == ".refresh":
        for friend in LIST_OF_FRIENDS:
            strings = get_data_for_user(friend)
            embed = discord.Embed(title=friend, description=strings[0] + "\n" + strings[1], color=discord.Colour.teal())
            await message.channel.send(embed=embed)
    if message.content == ".flamehani":
        if get_last_ranking("alostaz47"):
            insult = random.choice(list_of_hani_insults)
            await message.channel.send(insult)
        else:
            await message.channel.send("You can't flame Hani just yet...")
            await message.channel.send("...but he does have a crippling addiction")
    if message.content == ".flamesandy":
        if get_last_ranking("alostaz47"):
            insult = random.choice(list_of_hani_insults)
            await message.channel.send(insult)
        else:
            await message.channel.send("I feel bad insulting Sandy now it's like kicking a dead deer")
    elif message.content == ".help":
        embed = discord.Embed(title="Command List and Information", description="This bot refreshes every minute to update members of peoples' TFT status.", color=discord.Colour.teal())
        embed.add_field(name="Refresh", value=".refresh: Displays recent information about users' last game and current ranking.", inline=False)
        embed.add_field(name="Help", value=".help: Displays this message.", inline=False)

        await message.channel.send(embed=embed)
    elif message.content == ".flamesandy":
        if get_last_ranking("SaltySandyHS"):
            flame_str = FLAME_MESSAGE_LIST[random.randint(0, 5)]
            await message.channel.send(flame_str)
        else:
            await message.channel.send("You can't flame Sandy just yet...")



@tasks.loop(seconds=60)
async def game_played_tracker():
    await client.wait_until_ready()
    channel_test = client.get_channel(458644594905710595)
    channel_rito_daddy = client.get_channel(700018369281261568)

    for friend in LIST_OF_FRIENDS:
        recent_match = get_most_recent_match(friend)
        if FRIENDS_LAST_GAME_PLAYED[friend] != recent_match and get_timedelta(recent_match) < 300:
            strings = get_data_for_user(friend)
            ranking_str = ""
            if get_last_ranking(friend):
                ranking_str = "bot 4"
            else:
                ranking_str = "top 4"
            embed = discord.Embed(title=friend + " went " + ranking_str, description=strings[0] + "\n" + strings[1], color=discord.Colour.teal())
            await channel_test.send(embed=embed)
            await channel_rito_daddy.send(embed=embed)
            FRIENDS_LAST_GAME_PLAYED[friend] = recent_match
        elif FRIENDS_LAST_GAME_PLAYED[friend] != recent_match:
            FRIENDS_LAST_GAME_PLAYED[friend] = recent_match

game_played_tracker.start()
client.run(os.getenv("DISCORD_TOKEN"))