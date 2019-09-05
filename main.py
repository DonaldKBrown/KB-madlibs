import asyncio
import logging
import os
from pykeybasebot import Bot, ContentType, Source
import sqlite3
from json import load as config_loader
from terminaltables import AsciiTable
from random import choice
from uuid import uuid4

with open('config.json','r') as f:
    config = config_loader(f)

cwd = os.path.dirname(os.path.abspath(__file__))
database_path = cwd + '/data.db'

if not os.path.exists(database_path):
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    cur.execute('CREATE TABLE games (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, status TEXT, submitted INTEGER, total INTEGER, category TEXT, title TEXT, file TEXT)')
    cur.execute('CREATE TABLE submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, game_id INTEGER, key TEXT, content TEXT)')
    conn.commit()
    conn.close()

logging.basicConfig(level=logging.DEBUG)

titles = {}
categories = {}
titles_path = cwd + '/titles/'
files = os.listdir(titles_path)
for file_ in files:
    file_path = titles_path + file_
    with open(file_path) as f:
        file_contents = f.read().split('###~~~###')
    title = file_contents[0].strip('\n')
    title_categories = []
    for category in file_contents[1].split('\n'):
        if len(category) < 3:
            continue
        if category.strip().upper() not in categories:
            categories[category.strip().upper()] = []
        categories[category.strip().upper()].append(file_)
        title_categories.append(category.strip().upper())
    keys = []
    for key_ in file_contents[2].split('\n'):
        key = key_.split('=')
        if len(key) < 2:
            continue
        keys.append({
            'KeyName' : key[0],
            'Prompt' : key[1]
        })
    text = file_contents[3].strip()
    titles[file_] = {
        'title' : title,
        'keys' : keys,
        'categories' : title_categories,
        'content' : text
    }

category_table_data = [['Category', 'Title Count']]
for category in categories:
    category_table_data.append([category, len(categories[category])])
category_table = AsciiTable(category_table_data)
category_table.inner_row_border = True
category_table.justify_columns[1] = 'right'
category_msg = f"""```
{category_table.table}
```"""

titles_table_data = [['File Name', 'Title', 'Replacements', 'Categories']]
for title in titles:
    titles_table_data.append([
        title,
        titles[title]['title'],
        len(titles[title]['keys']),
        ', '.join(titles[title]['categories'])
    ])
titles_table = AsciiTable(titles_table_data)
titles_table.inner_row_border = True
titles_table.justify_columns[3] = 'right'
titles_msg = f"""```
{titles_table.table}
```"""

help_data = [
    ['Command', 'Info'],
    ['!help', 'Print this message'],
    ['!request', 'Request a random title.'],
    ['!request <category>', 'Request a random title from the given category'],
    ['!accept <gameid>', 'Accept and start the given game.'],
    ['!shuffle <gameid>', 'Choose another title from the same category for the\
\ngiven game. Only works on pending games.'],
    ['!cancel <gameid>', 'Ends/declines the given game.'],
    ['!categories', 'List available categories and their title counts'],
    ['!titles', 'List all titles and their categories.'],
    ['!start <file_name>', 'Start a game using the given file name, obtained through !titles.'],
    ['!games', 'List all games you are involved in.'],
    ['!status <gameid>', 'List a game\'s current status.\nFinished games reprint final result.'],
    ['!submit <gameid> <word>', 'Submit the word as the next key to the given game.\nOmitting <gameid> submits for your most recent active game.']
]
help_table = AsciiTable(help_data)
help_table.inner_row_border = True
help_msg = f"""```
{help_table.table}  
```"""

game_msg = """Your game:
    ID: {gameid}
    Categories: {category}
    Title: {title} (from file `{file}`)
To accept, type `!accept {gameid}`. To select a different title, type `!shuffle {gameid}`. To decline and cancel this game entirely, type `!cancel {gameid}`."""

selected_game_msg = """Your game:
    ID: {gameid}
    Categories: {category}
    Title: {title} (from file `{file}`)
Your first prompt is:
`{prompt}`
Type `!submit <text>` to submit your answer."""

def new_game(sender, category=None, gameid=None, file_=None):
    if not file_:
        random = False
        chosen = False
        if not category:
            category = choice(list(categories.keys()))
            random = True
        file_ = choice(categories[category])
        title = titles[file_]
    else:
        title = titles[file_]
        random = False
        chosen = True
        category = 'chosen_from_file'
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    if not gameid:
        if random:
            cur.execute(
                'INSERT INTO games (user, status, submitted, total, title, file) VALUES (?, "pending", 0, ?, ?, ?)',
                [sender, len(title['keys']), title['title'], file_]
            )
        else:
            if chosen:
                status = 'active'
            else:
                status = 'pending'
            cur.execute(
                'INSERT INTO games (user, status, submitted, total, category, title, file) VALUES (?, ?, 0, ?, ?, ?, ?)',
                [sender, status, len(title['keys']), category, title['title'], file_]
            )
        conn.commit()
        gameid = cur.execute(
            'SELECT * FROM games WHERE user = ? ORDER BY id DESC',
            [sender]
        ).fetchone()[0]
    else:
        cur.execute(
            'UPDATE games SET title = ?, total = ?, file = ? WHERE id = ? AND user = ?',
            [title['title'], len(title['keys']), file_, gameid, sender]
        )
        conn.commit()
    conn.close()
    return {
        'title' : title['title'],
        'file' : file_,
        'category' : ', '.join(title['categories']),
        'gameid' : gameid,
        'chosen' : chosen,
        'prompt' : title['keys'][0]['Prompt']
    }

def owns_game(sender, game_id):
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    result = cur.execute('SELECT * FROM games WHERE user = ? AND id = ?', [sender, game_id]).fetchone()
    conn.close()
    if result:
        return result
    else:
        return False

def list_games(sender):
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    results = cur.execute('SELECT * FROM games WHERE user = ?', [sender]).fetchall()
    conn.close()
    if not results:
        return "You have no games!"
    else:
        games_table_data = [['Game ID', 'Title', 'Status', 'Submitted Words', 'Total Words']]
        for result in results:
            games_table_data.append([
                result[0],
                result[6],
                result[2],
                result[3],
                result[4]
            ])
        games_table = AsciiTable(games_table_data)
        games_table.inner_row_border = True
        return f"```{games_table.table}```"

def get_last_active(user):
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    matched_game = cur.execute('SELECT * FROM games WHERE status = "active" AND user = ? ORDER BY id DESC', [user]).fetchone()
    conn.close()
    return matched_game

def final_results(gameid):
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    title = titles[cur.execute('SELECT file FROM games WHERE id = ?', [gameid]).fetchone()[0]]
    rows = cur.execute('SELECT * FROM submissions WHERE game_id = ?', [gameid]).fetchall()
    replacements = {}
    for row in rows:
        replacements[row[2]] = row[3]
    full_text = title['content'].format(**replacements)
    conn.close()
    return f'{title["title"]}\n{full_text}'

class Handler:
    async def __call__(self, bot, event):
        if event.source != Source.REMOTE:
            return
        sender = event.msg.sender.username
        if event.msg.channel.name in [f"{config['bot_name']},{sender}", f"{sender},{config['bot_name']}"]:
            channel = event.msg.channel
            body = event.msg.content.text.body.split(' ')
            if body[0].lower() == '!help':
                await bot.chat.send(channel.replyable_dict(), help_msg)
            elif body[0].lower() == '!categories':
                await bot.chat.send(channel.replyable_dict(), category_msg)
            elif body[0].lower() == '!games':
                await bot.chat.send(channel.replyable_dict(), list_games(sender))
            elif body[0].lower() == '!titles':
                await bot.chat.send(channel.replyable_dict(), titles_msg)
            elif body[0].lower() == '!start':
                if len(body) != 2:
                    await bot.chat.send(channel.replyable_dict(), 'You must provide a file name to start a game.')
                    return None
                if body[1].lower() not in titles:
                    await bot.chat.send(channel.replyable_dict(), 'Could not find that file. Use `!titles` to see available files.')
                    return None
                game_info = new_game(sender, None, None, body[1].lower())
                await bot.chat.send(channel.replyable_dict(), selected_game_msg.format(**game_info))
            elif body[0].lower() == '!request':
                if len(body) < 2:
                    game_info = new_game(sender)
                else:
                    category = ' '.join(body[1:]).upper()
                    if category not in categories:
                        await bot.chat.send(channel.replyable_dict(), 'That is not a valid category.')
                        return
                    game_info = new_game(sender, category)
                await bot.chat.send(channel.replyable_dict(), game_msg.format(**game_info))
            elif body[0].lower() == '!shuffle':
                if len(body) != 2:
                    await bot.chat.send(channel.replyable_dict(), 'You must supply exactly one game ID to shuffle (use `!games` to find pending games).')
                else:
                    matched_game = owns_game(sender, body[1])
                    if not matched_game:
                        await bot.chat.send(channel.replyable_dict(), 'That is not your game. Use `!games` to see your games.')
                        return None
                    if matched_game[2] != 'pending':
                        await bot.chat.send(channel.replyable_dict(), 'You cannot shuffle a non-pending game.')
                    else:
                        game_info = new_game(sender, matched_game[5], body[1])
                        await bot.chat.send(channel.replyable_dict(), game_msg.format(**game_info))
            elif body[0].lower() == '!cancel':
                if len(body) != 2:
                    await bot.chat.send(channel.replyable_dict(), 'You must supply exactly one game ID to cancel.')
                else:
                    matched_game = owns_game(sender, body[1])
                    if not matched_game:
                        await bot.chat.send(channel.replyable_dict(), 'This is not your game. Use `!games` to see your games.')
                    else:
                        if matched_game[2] in ['pending','active']:
                            conn = sqlite3.connect(database_path)
                            cur = conn.cursor()
                            cur.execute('UPDATE games SET status = "canceled" WHERE id = ?', [body[1]])
                            conn.commit()
                            conn.close()
                            await bot.chat.send(channel.replyable_dict(), f'You have canceled game ID {body[1]}.')
                        else:
                            await bot.chat.send(channel.replyable_dict(), 'You cannot cancel a game that has been completed or already canceled.')
            elif body[0].lower() == '!accept':
                if len(body) != 2:
                    await bot.chat.send(channel.replyable_dict(), 'You must supply exactly one game ID to accept.')
                    return None
                matched_game = owns_game(sender, body[1])
                if not matched_game:
                    await bot.chat.send(channel.replyable_dict(), 'This is not your game. Use `!games` to see your games.')
                    return None
                if matched_game[2] != 'pending':
                    await bot.chat.send(channel.replyable_dict(), 'The given game is not pending. Use `!games` to view the status of all of your current games.')
                    return None
                conn = sqlite3.connect(database_path)
                cur = conn.cursor()
                cur.execute('UPDATE games SET status = "active" WHERE id = ?', [body[1]])
                conn.commit()
                conn.close()
                first_key = titles[matched_game[7]]['keys'][0]['Prompt']
                await bot.chat.send(channel.replyable_dict(), f'It has begun!\nType `!submit {body[1]} <your submission>` to submit your word.\nYour first prompt is: `{first_key}`')
            elif body[0].lower() == '!status':
                if len(body) != 2:
                    await bot.chat.send(channel.replyable_dict(), 'You must supply exactly one game ID to get status/final results.')
                    return None
                matched_game = owns_game(sender, body[1])
                if not matched_game:
                    await bot.chat.send(channel.replyable_dict(), 'This is not your game. Use `!games` to see your games.')
                    return None
                if matched_game[2] == 'pending':
                    await bot.chat.send(channel.replyable_dict(), f'This game is pending.\nTitle: {matched_game[6]}\nType `!accept {body[1]}` to accept or `!shuffle {body[1]}` to choose a new title.')
                elif matched_game[2] == 'canceled':
                    await bot.chat.send(channel.replyable_dict(), 'You cancelled this game!')
                elif matched_game[2] == 'active':
                    current_prompt = titles[matched_game[7]]['keys'][matched_game[3]]['Prompt']
                    title = matched_game[6]
                    await bot.chat.send(channel.replyable_dict(), f'Title: {title}\nCurrent Prompt: {current_prompt}')
                elif matched_game[2] == 'completed':
                    await bot.chat.send(channel.replyable_dict(), final_results(body[1]))
            elif body[0].lower() == '!submit':
                if len(body) < 2:
                    await bot.chat.send(channel.replyable_dict(), 'You must provide at least the planned submission text.')
                    return None
                matched_game = owns_game(sender, body[1])
                s = 2
                if not matched_game:
                    matched_game = get_last_active(sender)
                    s = 1
                    if not matched_game:
                        await bot.chat.send(channel.replyable_dict(), 'Could not find an active game for this submission. Use `!games` to see your games.')
                        return None
                if matched_game[2] != 'active':
                    await bot.chat.send(channel.replyable_dict(), 'That game is not currently active.')
                    return None
                conn = sqlite3.connect(database_path)
                cur = conn.cursor()
                submitted_text = ' '.join(body[s:])
                key_name = titles[matched_game[7]]['keys'][matched_game[3]]['KeyName']
                cur.execute('INSERT INTO submissions (game_id, key, content) VALUES (?, ?, ?)', [matched_game[0], key_name, submitted_text])
                conn.commit()
                next_key = matched_game[3] + 1
                if next_key == matched_game[4]:
                    await bot.chat.send(channel.replyable_dict(), 'You finished! Wait while I get your final results...')
                    cur.execute('UPDATE games SET status = "completed", submitted = ? WHERE id = ?', [next_key, matched_game[0]])
                    conn.commit()
                    conn.close()
                    await bot.chat.send(channel.replyable_dict(), final_results(matched_game[0]))
                    return None
                next_prompt = titles[matched_game[7]]['keys'][next_key]['Prompt']
                cur.execute('UPDATE games SET submitted =? WHERE id = ?', [next_key, matched_game[0]])
                conn.commit()
                conn.close()
                await bot.chat.send(channel.replyable_dict(), f'Got it! Your next prompt is:\n`{next_prompt}`')
        return

listen_options = {
    "local" : True,
    "wallet" : True,
    "dev" : True,
    "hide-exploding" : False,
    "filter_channel" : None,
    "filter_channels" : None
}

bot = Bot(username=config['bot_name'], paperkey=config['paper_key'], handler=Handler())
asyncio.run(bot.start(listen_options=listen_options))