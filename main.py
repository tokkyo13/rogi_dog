import discord
import subprocess
import os

# インスタンスを作成
client = discord.Client()

# 読み上げ用 channel id を設定
# text-to-speech の id
# channel の id は discord で開発者モードをONにすると見れるようになる
READ_CHANNEL_ID = 845172576673071114

# トークン
TOKEN = os.environ.get("DISCORD_TOKEN")


# openjtalk をサブプロセスで実行する関数
def jtalk(tt):
    open_jtalk = ["open_jtalk"]
    mech = ["-x", "/var/lib/mecab/dic/open-jtalk/naist-jdic"]
    htsvoice = ["-m", "./hts_voice/mei/mei_happy.htsvoice"]
    speed = ["-r", "1.0"]
    outwav = ["-ow", "./message.wav"]
    cmd = open_jtalk + mech + htsvoice + speed + outwav
    subprocess.run(cmd, input=tt.encode())


# クライアントの初期設定が終わったら実行
@client.event
async def on_ready():
    print(f"I have logged in as {client.user}")


# メッセージが送信されたら実行
@client.event
async def on_message(message):
    # チャンネルが読み上げ用でなければ無視
    if message.channel.id != READ_CHANNEL_ID:
        return

    # 発言者が bot なら無視
    if message.author.bot:
        return

    # 発言者がボイスチャンネルでミュート状態でなければエラーメッセージ
    if message.author.voice is None or not message.author.voice.self_mute:
        await message.channel.send("ボイスチャンネルにミュートの状態で参加してください")
        return

    # voice channel に接続していなければ接続する
    if message.guild.voice_client is None:
        await message.author.voice.channel.connect()

    # openjtalk でメッセージのテキストから wav ファイルを作り
    # ffmpeg で bytes-like object に変換
    jtalk(message.content)
    audio_source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio("message.wav", before_options="-guess_layout_max 0"),
        volume=0.5,
    )

    # 作ったオーディオソースを再生
    message.guild.voice_client.play(audio_source)


# 誰かの voice state が変化したとき実行
@client.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client

    # voice_client が None なら voice channel に接続していない
    if voice_state is None:
        return

    # voice_client.channel で bot がいま接続してる voice channel が取得できる
    # メンバーが一人しかいなければ抜ける
    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


client.run(TOKEN)
