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
import traceback
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    host=os.environ.get("HOST"),
    database=os.environ.get("DATABASE"),
    user=os.environ.get("USER"),
    password=os.environ.get("PASSWORD")
)

cur = conn.cursor()

NEEDS_UPDATE = {}

RANKING_DICT = {"CHALLENGER":0, "GRANDMASTER":1, "MASTER":2, "DIAMOND":3, "PLATINUM":4, "GOLD":5, "SILVER":6, "BRONZE":7, "IRON":8}

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
FLAME_MESSAGE_13 = "cosine waving i see you"
FLAME_MESSAGE_14 = "new master duel video dropped"
FLAME_MESSAGE_15 = "at least he can finish a tft game quickly"
FLAME_MESSAGE_16 = "<:hanium:887502989500223498>"

FLAME_MESSAGE_LIST_HANI = [FLAME_MESSAGE_1, FLAME_MESSAGE_2, FLAME_MESSAGE_3, FLAME_MESSAGE_4, FLAME_MESSAGE_5, FLAME_MESSAGE_6, FLAME_MESSAGE_7, FLAME_MESSAGE_10, FLAME_MESSAGE_11, FLAME_MESSAGE_12, FLAME_MESSAGE_14, FLAME_MESSAGE_16]
FLAME_MESSAGE_LIST_SANDY = [FLAME_MESSAGE_1, FLAME_MESSAGE_2, FLAME_MESSAGE_3, FLAME_MESSAGE_4, FLAME_MESSAGE_5, FLAME_MESSAGE_8, FLAME_MESSAGE_9, FLAME_MESSAGE_12, FLAME_MESSAGE_13]
FLAME_MESSAGE_LIST_JREISS = [FLAME_MESSAGE_1, FLAME_MESSAGE_2, FLAME_MESSAGE_4, FLAME_MESSAGE_5, FLAME_MESSAGE_6, FLAME_MESSAGE_10, FLAME_MESSAGE_12, FLAME_MESSAGE_15]

headers = {"X-Riot-Token": os.environ.get("RIOT_API_TOKEN")}

items_file = open('items.json')
items_data = json.load(items_file)

client = discord.Client()


# gets all servers player is in
def get_servers_from_player(user):
    query = '''SELECT server_id FROM player_server_relation WHERE player_name=\'''' + user + '''\''''
    cur.execute(query)

    server_list = cur.fetchall()
    return [server[0] for server in server_list]


# gets list of players from db
def get_players_from_db():
    query = '''SELECT name FROM player'''
    cur.execute(query)

    player_list = cur.fetchall()
    return [player[0].rstrip() for player in player_list]

# gets last game played from db
def get_last_game(user):

    query = '''SELECT match_id FROM player WHERE name=\'''' + user + '''\''''
    cur.execute(query)

    last_game = cur.fetchall()
    return last_game[0][0].rstrip()

# get default channel from server
def get_channel_from_server(server):

    query = '''SELECT default_channel FROM server WHERE id=''' + str(server)
    cur.execute(query)

    channel_name = cur.fetchall()
    return channel_name[0][0]

# gets list of servers from db
def get_servers_from_db():
    query = '''SELECT id FROM server'''
    cur.execute(query)

    server_db = cur.fetchall()
    server_list = []

    for element in server_db:
        server_list.append(element[0])

    return server_list

# adds server if not in db
def add_server_to_db(message):
    server = message.guild.id
    channel = message.channel.id

    query = '''SELECT * FROM server WHERE id=''' + str(server)
    cur.execute(query)

    server_db = cur.fetchall()

    if len(server_db) == 0:
        query = '''INSERT INTO server(id, prefix, default_channel) VALUES (''' + str(server) + ''', \'.\', ''' + str(channel) + ''')'''
        cur.execute(query)
        conn.commit()


# gets list of all players from server
def get_all_players_from_server(server):

    query = '''SELECT player_name FROM player_server_relation WHERE server_id=''' + str(server)
    cur.execute(query)

    user_list = cur.fetchall()

    users_in_server = []
    for element in user_list:
        users_in_server.append(element[0].rstrip())

    return users_in_server


# adds user if not in db
def add_user_to_db(user):

    query = '''SELECT * FROM player WHERE name=\'''' + user + '''\''''
    cur.execute(query)

    user_db = cur.fetchall()

    if len(user_db) == 0:
        query = '''INSERT INTO player(name) VALUES (\'''' + user + '''\')'''
        cur.execute(query)
        conn.commit()


# adds user and checks relation in db
def add_user(message):
    server = message.guild.id
    user = " ".join(message.content.split(" ")[1:])

    NEEDS_UPDATE[user] = None

    query = '''SELECT * FROM player_server_relation WHERE player_name=\'''' + user + '''\' AND server_id=''' + str(server)
    cur.execute(query)

    check_relation = cur.fetchall()

    if len(check_relation) == 0:
        add_server_to_db(message)
        add_user_to_db(user)

        query = '''INSERT INTO player_server_relation(player_name, server_id) VALUES (\'''' + user + '''\', ''' + str(server) + ''')'''
        cur.execute(query)
        conn.commit()


# retrieves user data as list of strings from db
def get_data_from_db(user):

    strings = []

    query = '''SELECT COUNT(*) FROM player WHERE name=\'''' + user + '''\''''
    cur.execute(query)

    if cur.fetchall()[0][0] > 0:
        query = '''SELECT * FROM player WHERE name=\'''' + user + '''\''''
        cur.execute(query)

        user_info = cur.fetchall()

        strings.append(user_info[0][0].rstrip())
        strings.append(user_info[0][1].rstrip())
        strings.append(time_to_timedelta(user_info[0][2]))
        strings.append(strings[0] + " went " + str(user_info[0][3]) + "/8.")
        strings.append(user_info[0][4].rstrip())
        strings.append(user_info[0][5].rstrip().replace("$", "\'").replace(";", "\n"))
        strings.append(user_info[0][6].rstrip())
        strings.append(user_info[0][7].rstrip())

        return strings


# helper to update or add row
def add_data_check(user):
    query = '''SELECT COUNT(*) FROM player WHERE name=\'''' + user + '''\''''
    cur.execute(query)

    if cur.fetchall()[0][0] != 1:
        return "ADD"
    else:
        return "UPDATE"


# updates user data if not in database
def update_data(user_list):

    for user in user_list:
        query = '''SELECT * from player where name=\'''' + user + '''\''''
        cur.execute(query)
        arr = cur.fetchall()

        if len(arr) == 0:
            get_data_for_user(user)
        # if no last game in db (new user) or needs update
        # then update data and remove user from list of needed updates
        elif arr[0][6] is None:
            get_data_for_user(user)
        elif user in list(NEEDS_UPDATE.keys()):
            get_data_for_user(user)
            NEEDS_UPDATE.pop(user)


# converts datetime to a timedelta string
def time_to_timedelta(timedelta_str):

    datetime_str = str(datetime.datetime.fromtimestamp(float(timedelta_str)))
    format = "%Y-%m-%d %H:%M:%S"
    datetime_obj = datetime.datetime.strptime(datetime_str, format)

    timedelta = (datetime.datetime.now() - datetime_obj)
    hours = timedelta.seconds // 3600
    minutes = timedelta.seconds // 60 - hours * 60
    seconds = timedelta.seconds - hours * 3600 - minutes * 60

    date_str = str(timedelta.days) + " days, " + str(hours) + " hours, " + str(minutes) + " minutes, and " + str(seconds) + " seconds ago, "
    return date_str


# compares ranks of users given the list of strings from user output
def compare_ranks(list_of_strings_1, list_of_strings_2):

    rank_str_1 = list_of_strings_1[1].rstrip()
    rank_str_2 = list_of_strings_2[1].rstrip()

    # check if unranked (different message content)
    if rank_str_1.split(" ")[-1] == "unranked.":
        if rank_str_2.split(" ")[-1] == "unranked.":
            return 0
        else:
            return 1
    elif rank_str_2.split(" ")[-1] == "unranked.":
        return -1

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


# pushes data for last game played to player table
def get_data_for_user(summoner_name):

    response_ids = json.loads(requests.get("https://na1.api.riotgames.com/tft/summoner/v1/summoners/by-name/" + summoner_name, headers=headers).content.decode())
    response_rank = json.loads(requests.get("https://na1.api.riotgames.com/tft/league/v1/entries/by-summoner/" + response_ids["id"], headers=headers).content.decode())

    # checks for ranked tft ranking only
    for queue in response_rank:
        if queue['queueType'] == 'RANKED_TFT':
            response_rank = queue

    # checks if user is unranked
    if len(response_rank) == 0:
        rank = summoner_name + " is currently unranked."
    else:
        rank = summoner_name + " is currently " + response_rank['tier'] + " " + response_rank['rank'] + ", " + str(response_rank['leaguePoints']) + " LP."

    response_matches = [get_most_recent_match(summoner_name)]

    response_recent_match = json.loads(requests.get("https://americas.api.riotgames.com/tft/match/v1/matches/" + response_matches[0], headers=headers).content.decode())
    timedelta = int(response_recent_match['info']['game_datetime'] / 1e3)

    last_placement = -1

    trait_str = ""
    comp_str = ""
    augment_str = ""

    # gets last placement, items for queried player
    for player in response_recent_match['info']['participants']:
        if player['puuid'] == response_ids['puuid']:
            if 'augments' in list(player.keys()):
                augment_str = ", ".join([augment.split("_")[2] for augment in player['augments']])
            for trait in player['traits']:
                if trait['tier_current'] != 0:
                    trait_str += str(trait['num_units']) + " " + trait['name'][5:] + " "
            # gets items and player units
            for unit in player['units']:
                comp_str += str(unit['tier']) + " star " + unit['character_id'][5:] + ": "
                if len(unit['items']) == 0:
                    comp_str += " No items\n"
                else:
                    comp_str += ", ".join(get_item_name(item_id) for item_id in unit['items']) + "\n"
            last_placement = player['placement']

    checker = add_data_check(summoner_name)

    if checker == "ADD":
        query = '''INSERT INTO player(name, rank, timedelta, last_placement, traits, comp, match_id, augments) 
        VALUES(\'''' + summoner_name + '''\', \'''' + str(rank) + '''\', ''' + str(timedelta) + ''', ''' + str(last_placement) + ''', \'''' + trait_str + '''\', \'''' + comp_str.replace("'", "$").replace("\n", ";") + '''\', \'''' + response_matches[0] + '''\', \'''' + augment_str + '''\')'''
        cur.execute(query)
    elif checker == "UPDATE":
        query = '''UPDATE player
        SET rank=\'''' + str(rank) + '''\', timedelta=''' + str(timedelta) + ''', last_placement=''' + str(last_placement) + ''', traits=\'''' + trait_str + '''\', comp=\'''' + comp_str.replace("'", "$").replace("\n", ";") + '''\', match_id=\'''' + response_matches[0] + '''\', augments=\'''' + augment_str + '''\' WHERE name=\'''' + summoner_name + '''\''''
        cur.execute(query)

    conn.commit()


# on message to discord channel
@client.event
async def on_message(message):
    try:
        # displays information for all players
        if message.content == ".refreshverbose":
            LIST_OF_FRIENDS = get_all_players_from_server(message.guild.id)
            update_data(LIST_OF_FRIENDS)
            FRIENDS_DATA = {}
            for friend in LIST_OF_FRIENDS:
                FRIENDS_DATA[friend] = get_data_from_db(friend)
            friend_strings_list = [i for i in list(FRIENDS_DATA.values()) if i]
            friend_strings_list.sort(key=functools.cmp_to_key(compare_ranks))
            for friend_strings in friend_strings_list:
                embed = discord.Embed(title=friend_strings[0], description=friend_strings[1] + "\n" + friend_strings[2] + friend_strings[3], color=discord.Colour.teal())
                # displays last comp played
                embed.add_field(name="Augments:", value="[1, 2, 3]: " + friend_strings[7], inline=False)
                embed.add_field(name="Last Comp:", value=friend_strings[4] + "\n\n" + friend_strings[5], inline=False)
                await message.channel.send(embed=embed)
        # refreshes verbose specified user
        elif message.content.split(" ")[0] == ".refreshverbose":
            LIST_OF_FRIENDS = get_all_players_from_server(message.guild.id)
            friend = " ".join(message.content.split(" ")[1:])
            update_data(LIST_OF_FRIENDS)
            get_data_from_db(friend)
            FRIENDS_DATA = {}
            for friend_loop in LIST_OF_FRIENDS:
                FRIENDS_DATA[friend_loop] = get_data_from_db(friend_loop)
            friend_strings_list = [friend_string for friend_string in list(FRIENDS_DATA.values()) if friend_string and friend_string[0] == friend]
            for friend_strings in friend_strings_list:
                embed = discord.Embed(title=friend_strings[0], description=friend_strings[1] + "\n" + friend_strings[2] + friend_strings[3], color=discord.Colour.teal())
                # displays last comp played
                embed.add_field(name="Augments:", value="[1, 2, 3]: " + friend_strings[7], inline=False)
                embed.add_field(name="Last Comp:", value=friend_strings[4] + "\n\n" + friend_strings[5], inline=False)
                await message.channel.send(embed=embed)
        # refreshes all users
        elif message.content == ".refresh":
            LIST_OF_FRIENDS = get_all_players_from_server(message.guild.id)
            update_data(LIST_OF_FRIENDS)
            for friend in LIST_OF_FRIENDS:
                get_data_from_db(friend)
            FRIENDS_DATA = {}
            for friend in LIST_OF_FRIENDS:
                FRIENDS_DATA[friend] = get_data_from_db(friend)
            friend_strings_list = [i for i in list(FRIENDS_DATA.values()) if i]
            friend_strings_list.sort(key=functools.cmp_to_key(compare_ranks))
            embed = discord.Embed(title="Refreshed Data", color=discord.Colour.teal())
            for friend_strings in friend_strings_list:
                embed.add_field(name=friend_strings[0], value=friend_strings[1], inline=False)
            await message.channel.send(embed=embed)
        # refreshes specified user
        elif message.content.split(" ")[0] == ".refresh":
            LIST_OF_FRIENDS = get_all_players_from_server(message.guild.id)
            friend = " ".join(message.content.split(" ")[1:])
            update_data(LIST_OF_FRIENDS)
            get_data_from_db(friend)
            FRIENDS_DATA = {}
            for friend_loop in LIST_OF_FRIENDS:
                FRIENDS_DATA[friend_loop] = get_data_from_db(friend_loop)
            friend_strings_list = [friend_string for friend_string in list(FRIENDS_DATA.values()) if friend_string and friend_string[0] == friend]
            for friend_strings in friend_strings_list:
                embed = discord.Embed(title=friend_strings[0], description=friend_strings[1], color=discord.Colour.teal())
                await message.channel.send(embed=embed)
        # flames hani
        elif message.content == ".flamehani":
            if get_last_ranking("alostaz47"):
                insult = random.choice(FLAME_MESSAGE_LIST_HANI)
                await message.channel.send(insult)
            else:
                await message.channel.send("You can't flame Hani just yet...\n...but he does have a crippling addiction")
        # flames sandy
        elif message.content == ".flamesandy":
            if get_last_ranking("SaltySandyHS"):
                insult = random.choice(FLAME_MESSAGE_LIST_SANDY)
                await message.channel.send(insult)
            else:
                await message.channel.send("I feel bad insulting Sandy now it's like kicking a dead deer")
        # flames jreiss
        elif message.content == ".flamejreiss":
            if get_last_ranking("ExistToCease"):
                insult = random.choice(FLAME_MESSAGE_LIST_JREISS)
                await message.channel.send(insult)
            else:
                await message.channel.send("He actually got a top 4 :o")
        elif message.content.split(" ")[0] == ".adduser":
            add_user(message)
            await message.channel.send(" ".join(message.content.split(" ")[1:]) + " has been added to the list of updated users for " + message.guild.name + ".")
        elif message.content.split(" ")[0] == ".deleteuser":
            await message.channel.send("Soon TM")
        # help command
        elif message.content == ".help":
            embed = discord.Embed(title="Command List and Information", description="This bot refreshes every minute to update members of peoples' TFT status.", color=discord.Colour.teal())
            embed.add_field(name="Refresh", value=".refresh: Displays recent information about users and their current ranking.\n.refresh [player_name]: Displays information about a specific user.", inline=False)
            embed.add_field(name="Refresh (Verbose)", value=".refreshverbose: Displays more information about users' last comps and game data.\n.refreshverbose [player_name]: Displays more information about a specific user.", inline=False)
            embed.add_field(name="Add User", value=".adduser: Add a user to the list of users with information in this server.", inline=False)
            embed.add_field(name="Flame a friend", value=".flamehani: Flames Hani if he bot 4ed the last game.\n.flamesandy: Flames Sandy if he bot 4ed the last game.\n.flamejreiss: Flames jreiss if he bot 4ed the last game.", inline=False)
            embed.add_field(name="Help", value=".help: Displays this message.", inline=False)

            await message.channel.send(embed=embed)
    except Exception as e:
        traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        await message.channel.send(traceback_str)


# sends message to channel if new game played, checks every 60 seconds
@tasks.loop(seconds=60)
async def game_played_tracker():
    await client.wait_until_ready()

    player_list = get_players_from_db()

    # personal test server, see error messages
    channel_test = client.get_channel(458644594905710595)
    try:
        for friend in player_list:
            recent_match = get_most_recent_match(friend)
            # if match not in history and match played within 5 minutes (avoids duplicate messages on startup)
            if get_last_game(friend) != recent_match and get_timedelta(recent_match) < 3000:
                get_data_for_user(friend)
                strings = get_data_from_db(friend)
                if get_last_ranking(friend):
                    ranking_str = "bot 4"
                else:
                    ranking_str = "top 4"
                embed = discord.Embed(title=friend + " went " + ranking_str, description=strings[1] + "\n" + strings[3], color=discord.Colour.teal())
                # displays last comp played
                embed.add_field(name="Augments:", value="[1, 2, 3]: " + strings[7], inline=False)
                embed.add_field(name="Last Comp:", value=strings[4] + "\n\n" + strings[5], inline=False)
                user_servers = get_servers_from_player(friend)
                for server in user_servers:
                    default_channel = client.get_channel(get_channel_from_server(server))
                    await default_channel.send(embed=embed)
                NEEDS_UPDATE[friend] = recent_match
            # just add older games to last game played
            elif get_last_game(friend) != recent_match:
                NEEDS_UPDATE[friend] = recent_match
    # prints exceptions in personal test channel
    except Exception as e:
        traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        await channel_test.send(traceback_str)

game_played_tracker.start()
client.run(os.getenv("DISCORD_TOKEN"))