import json
import discord
from discord.ext import tasks
import requests
import datetime
import os
from dotenv import load_dotenv
import random
import roman
import functools

load_dotenv()

LIST_OF_FRIENDS = ["SaltySandyHS", "alostaz47", "The Number 3", "ExistToCease", "gura tft player", "gamesuxbtw"]
FRIENDS_LAST_GAME_PLAYED = {"SaltySandyHS":None, "alostaz47":None, "The Number 3":None, "ExistToCease":None, "gura tft player":None, "gamesuxbtw":None}

FLAME_MESSAGE_1 = "Hey what happened :slight_smile:"
FLAME_MESSAGE_2 = ":slight_smile:"
FLAME_MESSAGE_3 = "It clicked btw"
FLAME_MESSAGE_4 = ":clown:"
FLAME_MESSAGE_5 = "It's just a warmup game"
FLAME_MESSAGE_6 = "sine waving i see you"
FLAME_MESSAGE_7 = "heyyy hani are you lowering your mmr for easier lobbies?"
FLAME_MESSAGE_8 = "imagine being lapped by hani"
FLAME_MESSAGE_9 = "dude clean your room instead of playing"
FLAME_MESSAGE_10 = "spoken like a true goldie"
FLAME_MESSAGE_11 = "best mental na btw"
FLAME_MESSAGE_12 = "Must've been a glitch!"

RANKING_DICT = {"CHALLENGER":0, "GRANDMASTER":1, "MASTER":2, "DIAMOND":3, "PLATINUM":4, "GOLD":5, "SILVER":6, "BRONZE":7, "IRON":8}

FLAME_MESSAGE_LIST_HANI = [FLAME_MESSAGE_1, FLAME_MESSAGE_2, FLAME_MESSAGE_3, FLAME_MESSAGE_4, FLAME_MESSAGE_5, FLAME_MESSAGE_6, FLAME_MESSAGE_7, FLAME_MESSAGE_10, FLAME_MESSAGE_11, FLAME_MESSAGE_12]
FLAME_MESSAGE_LIST_SANDY = [FLAME_MESSAGE_1, FLAME_MESSAGE_2, FLAME_MESSAGE_3, FLAME_MESSAGE_4, FLAME_MESSAGE_5, FLAME_MESSAGE_8, FLAME_MESSAGE_9, FLAME_MESSAGE_12]

headers = {"X-Riot-Token": os.environ.get("RIOT_API_TOKEN")}

items_file = open('items.json')
items_data = json.load(items_file)

client = discord.Client()


# compares ranks of users given the list of strings from user output
def compare_ranks(list_of_strings_1, list_of_strings_2):

    rank_str_1 = list_of_strings_1[0]
    rank_str_2 = list_of_strings_2[0]

    rank_1 = RANKING_DICT.get(rank_str_1.split(" ")[-4])
    rank_2 = RANKING_DICT.get(rank_str_2.split(" ")[-4])

    div_1 = rank_str_1.split(" ")[-3][:-1]
    div_2 = rank_str_2.split(" ")[-3][:-1]

    lp_1 = int(rank_str_1.split(" ")[-2])
    lp_2 = int(rank_str_2.split(" ")[-2])

    # if rank (challenger, gm, etc.) greater
    if rank_1 < rank_2:
        return -1
    elif rank_1 > rank_2:
        return 1
    else:
        # if division (i, ii, iii) better
        if roman.fromRoman(div_1) < roman.fromRoman(div_2):
            return -1
        elif roman.fromRoman(div_1) > roman.fromRoman(div_2):
            return 1
        else:
            # if lp greater
            if lp_1 > lp_2:
                return -1
            elif lp_2 < lp_1:
                return 1
            else:
                return 0


# returns the item name for an item id
def get_item_name(item_id):
    for item in items_data:
        if item['id'] == item_id:
            return item['name']
    # placeholder while trying to figure out items
    return ""


# returns the difference in time between now and the match selected
def get_timedelta(match_id):
    response_recent_match = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/" + match_id, headers=headers).content.decode())

    timedelta = datetime.datetime.now() - datetime.datetime.fromtimestamp(response_recent_match['info']['game_datetime'] / 1e3)

    return timedelta.seconds


# returns True if the player got bot 4 in their last game
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


# returns the most recent match id for a player
def get_most_recent_match(summoner_name):

    response_ids = json.loads(requests.get("https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/" + summoner_name, headers=headers).content.decode())

    response_matches = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/by-puuid/" + response_ids['puuid'] + "/ids?count=1", headers=headers).content.decode())
    return response_matches[0]


# returns two strings, one with rank info and one with last game played info
def get_data_for_user(summoner_name):

    strings = []

    response_ids = json.loads(requests.get("https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/" + summoner_name, headers=headers).content.decode())
    response_rank = json.loads(requests.get("https://na1.api.riotgames.com/tft/league/v1/entries/by-summoner/" + response_ids["id"], headers=headers).content.decode())

    # checks for ranked tft ranking only
    for queue in response_rank:
        if queue['queueType'] == 'RANKED_TFT':
            response_rank = queue

    strings.append(summoner_name + " is currently " + response_rank['tier'] + " " + response_rank['rank'] + ", " + str(response_rank['leaguePoints']) + " LP.")

    response_matches = [get_most_recent_match(summoner_name)]

    response_recent_match = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/" + response_matches[0], headers=headers).content.decode())

    timedelta = datetime.datetime.now() - datetime.datetime.fromtimestamp(response_recent_match['info']['game_datetime'] / 1e3)
    hours = timedelta.seconds//3600
    minutes = timedelta.seconds//60 - hours * 60
    seconds = timedelta.seconds - hours * 3600 - minutes * 60

    rank = -1

    # gets rank, items for queried player
    strings.append("")
    strings.append("")
    for player in response_recent_match['info']['participants']:
        if player['puuid'] == response_ids['puuid']:
            for trait in player['traits']:
                if trait['tier_current'] != 0:
                    strings[1] += str(trait['num_units']) + " " + trait['name'][5:] + " "
            # gets items and player units
            for unit in player['units']:
                strings[2] += str(unit['tier']) + " star " + unit['character_id'][5:] + ": "
                if len(unit['items']) == 0:
                    strings[2] += " No items\n"
                else:
                    strings[2] += ", ".join(get_item_name(item_id) for item_id in unit['items']) + "\n"
            rank = player['placement']

    strings.append(str(timedelta.days) + " days, " + str(hours) + " hours, " + str(minutes) + " minutes, " + str(seconds) + " seconds ago, ")
    strings.append(summoner_name + " finished " + str(rank) + "/8.")

    return strings


# on message to discord channel
@client.event
async def on_message(message):
    # displays information for all players
    if message.content == ".refresh":
        friend_strings_list = [get_data_for_user(friend) for friend in LIST_OF_FRIENDS]
        friend_strings_list.sort(key=functools.cmp_to_key(compare_ranks))
        for friend_strings in friend_strings_list:
            friend = friend_strings[0].split(" ")[0]
            if friend == "alostaz47" or friend == "SaltySandyHS":
                embed = discord.Embed(title=friend, description=friend_strings[0] + "\n" + friend_strings[3] + " " + friend_strings[4], color=discord.Colour.teal())
                # displays last comp played
                embed.add_field(name="Last Comp:", value=friend_strings[1] + "\n\n" + friend_strings[2], inline=False)
                await message.channel.send(embed=embed)
    # flames hani
    if message.content == ".flamehani":
        if get_last_ranking("alostaz47"):
            insult = random.choice(FLAME_MESSAGE_LIST_HANI)
            await message.channel.send(insult)
        else:
            await message.channel.send("You can't flame Hani just yet...")
            await message.channel.send("...but he does have a crippling addiction")
    # flames sandy
    if message.content == ".flamesandy":
        if get_last_ranking("SaltySandyHS"):
            insult = random.choice(FLAME_MESSAGE_LIST_SANDY)
            await message.channel.send(insult)
        else:
            await message.channel.send("I feel bad insulting Sandy now it's like kicking a dead deer")
    # help command
    elif message.content == ".help":
        embed = discord.Embed(title="Command List and Information", description="This bot refreshes every minute to update members of peoples' TFT status.", color=discord.Colour.teal())
        embed.add_field(name="Refresh", value=".refresh: Displays recent information about users' last game and current ranking.", inline=False)
        embed.add_field(name="Flame a friend", value=".flamehani: Flames Hani if he bot 4ed the last game\n.flamesandy: Flames Sandy if he bot 4ed the last game", inline=False)
        embed.add_field(name="Help", value=".help: Displays this message.", inline=False)

        await message.channel.send(embed=embed)


# sends message to channel if new game played, checks every 60 seconds
@tasks.loop(seconds=60)
async def game_played_tracker():
    await client.wait_until_ready()
    # test -> general and pat harem -> rito daddy
    channel_test = client.get_channel(458644594905710595)
    channel_rito_daddy = client.get_channel(926942218974019665)

    for friend in LIST_OF_FRIENDS:
        recent_match = get_most_recent_match(friend)
        # if match not in history and match played within 5 minutes (avoids duplicate messages on startup)
        if FRIENDS_LAST_GAME_PLAYED[friend] != recent_match and get_timedelta(recent_match) < 300:
            strings = get_data_for_user(friend)
            ranking_str = ""
            if get_last_ranking(friend):
                ranking_str = "bot 4"
            else:
                ranking_str = "top 4"
            embed = discord.Embed(title=friend + " went " + ranking_str, description=strings[0] + "\n" + strings[4], color=discord.Colour.teal())
            # displays last comp played
            embed.add_field(name="Last Comp:", value=strings[1] + "\n\n" + strings[2], inline=False)
            await channel_test.send(embed=embed)
            await channel_rito_daddy.send(embed=embed)
            FRIENDS_LAST_GAME_PLAYED[friend] = recent_match
        # just add older games to last game played
        elif FRIENDS_LAST_GAME_PLAYED[friend] != recent_match:
            FRIENDS_LAST_GAME_PLAYED[friend] = recent_match

game_played_tracker.start()
client.run(os.getenv("DISCORD_TOKEN"))