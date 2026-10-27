import discord
from discord import app_commands
from collections import deque
from random import randint
import sqlite3
import json

db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule (
    user_id INTEGER PRIMARY KEY,
    data TEXT NOT NULL DEFAULT '{}'
)
""")

select_day = [
    app_commands.Choice(name = name, value = name)
    for name in ['월', '화', '수', '목', '금']
]
mention_choice = [
    app_commands.Choice(name = name, value = name)
    for name in ['True', 'False']
]

from config import TOKEN

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user}")

@bot.tree.command(
    name = '스케줄등록',
    description = '자신의 스케줄을 등록합니다.'
)
@app_commands.describe(
    요일 = '요일을 하나 선택해주세요.',
    일정 = '7교시, 방과후, 야자1타임, 야자2타임 순서대로 입력해주세요(O, X, 공백없이)'
)
@app_commands.choices(요일 = select_day)
async def 스케줄등록(interaction: discord.Interaction, 요일: app_commands.Choice[str], 일정: str) :
    user_id = interaction.user.id
    selected_day = 요일.value

    embed = discord.Embed(title = '스케줄 등록 결과')

    cursor.execute(
        "SELECT data FROM schedule WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()

    if result is None :
        data = {}
    else :
        data = json.loads(result[0])

    data[selected_day] = 일정

    cursor.execute("""
        INSERT INTO schedule (
            user_id, data
        )
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            data = excluded.data
    """, (user_id, json.dumps(data, ensure_ascii = False)))
    db.commit()

    embed.add_field(
        name = f'{selected_day}요일',
        value = f"""
7교시 : {일정[0]}
방과후 : {일정[1]}
야자1타임 : {일정[2]}
야자2타임 : {일정[3]}
""", 
        inline = False
    )

    await interaction.response.send_message(embed = embed)

@bot.tree.command(
    name = '스케줄조회',
    description = '해당 사용자의 스케줄을 조회합니다.'
)
@app_commands.describe(
    사용자 = '서버 인원 중에서 입력해주세요.',
    요일 = '확인할 요일을 선택해주세요.',
    멘션하기 = '일정이 설정되있지 않다면 멘션합니다.'
)
@app_commands.choices(
    요일 = select_day,
    멘션하기 = mention_choice
)
async def 스케줄조회(interaction: discord.Interaction, 사용자: discord.Member, 요일: app_commands.Choice[str], 멘션하기: app_commands.Choice[str]) :
    user_id = 사용자.id
    embed = discord.Embed(title = '스케줄 조회 결과')
    selected_day = 요일.value
    selected_mention = 멘션하기.value

    if selected_mention == 'False' :
        selected_mention = False

    cursor.execute(
        "SELECT data FROM schedule WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()

    if result is None :
        embed.add_field(
            name = '',
            value = '해당 사용자가 스케줄 등록을 하지 않았습니다.',
            inline = False
        )
        if selected_mention :
            await interaction.response.send_message(
                content = f"<@{user_id}>",
                embed = embed
            )
        else :
            await interaction.response.send_message(embed = embed)
        return
    else :
        data = json.loads(result[0])
    
    if selected_day not in data :
        embed.add_field(
            name = '',
            value = f'해당 사용자가 {selected_day}요일 스케줄 등록을 하지 않았습니다.',
            inline = False
        )
        if selected_mention :
            await interaction.response.send_message(
                content = f"<@{user_id}>",
                embed = embed
            )
        else :
            await interaction.response.send_message(embed = embed)
        return

    else :
        rst = data[selected_day]

        embed.add_field(
        name = f'{selected_day}요일',
        value = f"""
7교시 : {rst[0]}
방과후 : {rst[1]}
야자1타임 : {rst[2]}
야자2타임 : {rst[3]}
""", 
        inline = False
        )

    if selected_mention :
        await interaction.response.send_message(
            content = f"<@{user_id}>",
            embed = embed
        )
    else :
        await interaction.response.send_message(embed = embed)

bot.run(TOKEN)