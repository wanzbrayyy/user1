from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    DocumentAttributeAudio,
    UserStatusOnline,
    UserStatusOffline,
    UserStatusRecently,
    UserStatusLastWeek,
    UserStatusLastMonth,
)
import time, psutil, requests, io, os, json, random, sys, traceback
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
import speech_recognition as sr
from pydub import AudioSegment
from datetime import datetime, timezone
import asyncio

API_ID = 25054644
API_HASH = "d9c07f75d488f15cb655049af0fb686a"
OWNER_ID = 7774371395
GEMINI_API_KEY = "AIzaSyCgdjMVeHrWdu8HVr-Hzj5NfxJGN7mTiXY"

RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"
LEAKOSINT_API_TOKEN = "7774371395:CPK2Ml23"
SESSION_NAME = "session"
DATA_FILE = "awan_data.json"
AFK_COOLDOWN = 600 # Cooldown dalam detik (10 menit)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
mode_public = False
start_time = time.time()
afk_data = {}
afk_replied_to = {}
me = None
user_interaction_state = {}

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"welcome": {}, "anti_link": {}, "shortlinks": {}, "afk": {"is_afk": False, "message": "", "since": 0}, "cloned_users": [], "message_tracker_enabled": False, "cloned_bots": [], "menfess_log": {}}, f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def load_afk_from_disk():
    global afk_data
    data = load_data()
    default_afk = {"is_afk": False, "message": "", "since": 0}
    afk_data = data.get("afk", default_afk)
    if not isinstance(afk_data, dict) or "is_afk" not in afk_data:
        afk_data = default_afk

def save_afk_to_disk():
    data = load_data()
    data["afk"] = afk_data
    save_data(data)

def cpu_safe():
    try:
        return f"{psutil.cpu_percent()}%"
    except:
        return "N/A"

def uptime_str():
    s = int(time.time() - start_time)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h} jam {m} menit {sec} detik"

def uptime_str_custom(s):
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{int(h)} jam {int(m)} menit {int(sec)} detik"

async def is_owner(sender):
    if sender is None: return False
    return sender.id == OWNER_ID

async def is_authorized(sender):
    if sender is None: return False
    if sender.id == OWNER_ID: return True
    data = load_data()
    cloned_users = data.get("cloned_users", [])
    return sender.id in cloned_users

async def get_target_user(event):
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        return await client.get_entity(reply_msg.sender_id)
    pattern_match = event.pattern_match.group(1)
    if pattern_match:
        entity = pattern_match.strip()
        try:
            if entity.isdigit():
                return await client.get_entity(int(entity))
            else:
                return await client.get_entity(entity)
        except:
            return None
    return None

def format_user_status(status):
    if status is None:
        return "Tidak diketahui"
    try:
        if isinstance(status, UserStatusOnline):
            return "Online"
        if isinstance(status, UserStatusOffline):
            ts = getattr(status, "was_online", None)
            if ts:
                if isinstance(ts, datetime):
                    return ts.strftime("%Y-%m-%d %H:%M:%S")
                return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
            return "Offline"
        if isinstance(status, UserStatusRecently):
            return "Terlihat baru-baru ini"
        if isinstance(status, UserStatusLastWeek):
            return "Terlihat dalam seminggu terakhir"
        if isinstance(status, UserStatusLastMonth):
            return "Terlihat dalam sebulan terakhir"
    except:
        pass
    return str(status)

async def find_first_message_date(chat_id, user_id, max_messages=20000):
    try:
        async for msg in client.iter_messages(chat_id, limit=max_messages, reverse=True):
            if msg.sender_id == user_id:
                return msg.date
    except:
        return None
    return None


@client.on(events.NewMessage(pattern=r'^/(start|menu)$'))
async def show_menu(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    mode_text = "PUBLIC" if mode_public else "SELF"
    menu = (
f"⚜️ONLY BASE BY MAVERICK⚜️\nMODE: {mode_text}\n\n"
"╔═══════════════ UTAMA ═══════════════╗\n"
"/ping - status bot\n"
"/whois <@user/reply> - info pengguna\n"
"/text <teks> - buat stiker teks\n"
"/afk [alasan] - set mode AFK\n"
"╠═══════════════ OWNER ═══════════════╣\n"
"/clone <@user/balas> - clone user\n"
"/unclone <@user/balas> - hapus clone\n"
"/clonelist - lihat daftar clone\n"
"/clonebot - clone bot lain\n"
"/eval <code> - eksekusi kode python\n"
"/osint <user> - cek info user\n"
"/trackmsg <on/off> - lacak pesan grup\n"
"╠══════════════ BROADCAST ═════════════╣\n"
"/cekuser - Cek semua pengguna\n"
"/cekgroup - Cek semua grup\n"
"/broadcast <msg> | <id> - Broadcast pesan\n"
"╠══════════════ SEARCH ════════════════╣\n"
"/ttsearch <kata>\n/ytsearch <kata>\n/pinterest <kata>\n/github <username>\n/botnik <query>\n"
"╠══════════════ DOWNLOADER ════════════╣\n"
"/twdl <url>\n/fbdl <url>\n/capcut <url>\n/scdl <judul>\n/ghdl <url>\n/igdl <url>\n"
"╠══════════════ MEDIA ═════════════════╣\n"
"/topdf (reply foto)\n/resize <WxH> (reply foto)\n/audiotext (reply voice/file)\n"
"╠══════════════ GROUP ═════════════════╣\n"
"/setwelcome <teks>\n/anti <on/off>\n/group\n"
"╠══════════════ FUN ═════════════════╣\n"
"/meme\n/fancy <teks>\n/quotes\n"
"╠══════════════ UTIL ══════════════════╣\n"
"/cuaca <kota>\n/cekip\n/crypto <symbol>\n/shortlink <url>\n/tr <lang> <text>\n/ud <term>\n/createweb\n/tempmail\n"
"╚════════════════════════════════════╝"
    )
    if await is_owner(sender) or event.outgoing:
        # Trying to edit a message that doesn't exist will fail
        # So we will just send a new one in case of error
        try:
            await event.edit(menu)
        except:
            await event.respond(menu)
    else:
        await event.reply(menu)

@client.on(events.NewMessage(pattern=r'^/self$', outgoing=True))
async def set_self(event):
    global mode_public
    if not await is_owner(await event.get_sender()): return
    mode_public = False
    await event.edit("📌 MODE: SELF")

@client.on(events.NewMessage(pattern=r'^/public$', outgoing=True))
async def set_public(event):
    global mode_public
    if not await is_owner(await event.get_sender()): return
    mode_public = True
    await event.edit("📌 MODE: PUBLIC")

@client.on(events.NewMessage(pattern=r'^/afk(?:\s+(.*))?$', outgoing=True))
async def set_afk(event):
    global afk_data, afk_replied_to
    if not await is_owner(await event.get_sender()): return
    afk_replied_to.clear()
    text = event.pattern_match.group(1)
    afk_data["is_afk"] = True
    afk_data["since"] = time.time()
    afk_data["message"] = text if text else "Saya sedang tidak di tempat (AFK)."
    save_afk_to_disk()
    await event.edit(f"**Mode AFK diaktifkan.**\nPesan: `{afk_data['message']}`")

@client.on(events.NewMessage(func=lambda e: not e.from_scheduled))
async def afk_handler(event):
    global afk_data, afk_replied_to
    if not me:
        return

    # Menonaktifkan AFK jika kita mengirim pesan
    if event.sender_id == me.id and afk_data.get("is_afk"):
        if not event.message.message.lower().startswith('/afk'):
            since = afk_data.get("since", time.time())
            afk_time = uptime_str_custom(time.time() - since)
            afk_data["is_afk"] = False
            afk_replied_to.clear()
            save_afk_to_disk()
            await client.send_message(
                await event.get_chat(),
                f"✅ **Mode AFK telah dinonaktifkan.**\nAnda AFK selama: `{afk_time}`"
            )
        return
    
    # Membalas pesan jika AFK aktif dan pesan dari orang lain
    if afk_data.get("is_afk") and event.sender_id != me.id:
        sender = await event.get_sender()
        if not sender or sender.bot:
            return

        # Cek Cooldown
        if event.chat_id in afk_replied_to and time.time() - afk_replied_to[event.chat_id] < AFK_COOLDOWN:
            return

        # Kirim pesan AFK jika di PM atau di-mention di grup
        if event.is_private or event.mentioned:
            since_ts = afk_data.get("since", time.time())
            uptime_afk = uptime_str_custom(time.time() - since_ts)
            reply_message = f"{afk_data.get('message')}\n\nSaya telah AFK selama: `{uptime_afk}`"
            
            await client.send_message(await event.get_chat(), reply_message)
            afk_replied_to[event.chat_id] = time.time()


@client.on(events.NewMessage(pattern=r'^/clone(?:\s+(.*))?$', outgoing=True))
async def clone_user(event):
    if not await is_owner(await event.get_sender()): return
    m = await event.edit("🔄 Memproses...")
    target_user = await get_target_user(event)
    if not target_user:
        await m.edit("❗️ Balas pesan pengguna atau berikan username/ID untuk di-clone.")
        return
    data = load_data()
    cloned_users = data.get("cloned_users", [])
    if target_user.id in cloned_users:
        await m.edit(f"✅ Pengguna **{target_user.first_name}** sudah ada dalam daftar clone.")
        return
    cloned_users.append(target_user.id)
    data["cloned_users"] = cloned_users
    save_data(data)
    await m.edit(f"✅ Pengguna **{target_user.first_name}** berhasil di-clone. Dia sekarang bisa menggunakan bot ini.")

@client.on(events.NewMessage(pattern=r'^/unclone(?:\s+(.*))?$', outgoing=True))
async def unclone_user(event):
    if not await is_owner(await event.get_sender()): return
    m = await event.edit("🔄 Memproses...")
    target_user = await get_target_user(event)
    if not target_user:
        await m.edit("❗️ Balas pesan pengguna atau berikan username/ID untuk di-unclone.")
        return
    data = load_data()
    cloned_users = data.get("cloned_users", [])
    if target_user.id not in cloned_users:
        await m.edit(f"❗️ Pengguna **{target_user.first_name}** tidak ditemukan dalam daftar clone.")
        return
    cloned_users.remove(target_user.id)
    data["cloned_users"] = cloned_users
    save_data(data)
    await m.edit(f"✅ Akses untuk **{target_user.first_name}** telah dicabut.")

@client.on(events.NewMessage(pattern=r'^/clonebot$', outgoing=True))
async def clone_bot_start(event):
    if not await is_owner(await event.get_sender()):
        return

    sender_id = event.sender_id
    user_interaction_state[sender_id] = "awaiting_bot_token"

    await event.edit("🤖 Silakan kirimkan token bot yang ingin Anda clone.")

@client.on(events.NewMessage(func=lambda e: e.sender_id in user_interaction_state and user_interaction_state[e.sender_id] == "awaiting_bot_token" and not e.message.message.startswith('/')))
async def handle_bot_token(event):
    sender_id = event.sender_id
    bot_token = event.message.text.strip()

    # Hapus state pengguna
    del user_interaction_state[sender_id]

    m = await event.reply("🔎 Memverifikasi token bot...")

    # Verifikasi token
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = await asyncio.to_thread(requests.get, url, timeout=10)

        if response.status_code == 200:
            bot_info = response.json().get("result", {})
            bot_username = bot_info.get("username", "N/A")
            bot_id = bot_info.get("id", "N/A")

            # Simpan token
            data = load_data()
            cloned_bots = data.get("cloned_bots", [])

            # Cek apakah bot sudah di-clone
            for bot in cloned_bots:
                if bot.get("token") == bot_token:
                    await m.edit(f"✅ Bot `@{bot_username}` sudah ada dalam daftar.")
                    return

            cloned_bots.append({"token": bot_token, "id": bot_id, "username": bot_username})
            data["cloned_bots"] = cloned_bots
            save_data(data)

            await m.edit(f"✅ Bot `@{bot_username}` berhasil di-clone dan tokennya disimpan.\n\n"
                         "**Catatan:** Fitur untuk menjalankan bot yang di-clone secara otomatis belum sepenuhnya fungsional. "
                         "Saat ini hanya token yang disimpan.")
        else:
            error_msg = response.json().get("description", "Unknown error")
            await m.edit(f"❌ Token bot tidak valid.\nError: `{error_msg}`")

    except requests.exceptions.RequestException as e:
        await m.edit(f"❌ Gagal memverifikasi token: {e}")
    except Exception as e:
        await m.edit(f"❌ Terjadi kesalahan: {e}")

@client.on(events.NewMessage(pattern=r'^/clonelist$', outgoing=True))
async def list_clones(event):
    if not await is_owner(await event.get_sender()): return
    m = await event.edit("🔄 Mengambil daftar clone...")
    data = load_data()
    cloned_users_ids = data.get("cloned_users", [])
    if not cloned_users_ids:
        await m.edit("Tidak ada pengguna yang di-clone.")
        return
    text = "👤 **Daftar Pengguna Clone:**\n\n"
    for user_id in cloned_users_ids:
        try:
            user = await client.get_entity(user_id)
            text += f"- {user.first_name} (`{user.id}`)\n"
        except Exception:
            text += f"- ❗️ Gagal mengambil info untuk ID `{user_id}`\n"
    await m.edit(text)

@client.on(events.NewMessage(pattern=r'^/cekuser$'))
async def cek_user(event):
    sender = await event.get_sender()
    if not await is_authorized(sender): return
    m = await event.reply("🔄 Mengambil daftar pengguna...")
    users = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_user and not dialog.entity.bot:
                users.append(f"- {dialog.name} (`{dialog.id}`)")

        if not users:
            await m.edit("Tidak ada pengguna yang ditemukan.")
            return

        output_message = "👤 **Daftar Pengguna:**\n\n" + "\n".join(users)

        if len(output_message) > 4096:
            await m.edit("Jumlah pengguna terlalu banyak, mengirim sebagai file...")
            with io.StringIO(output_message) as f:
                f.name = "users.txt"
                await client.send_file(event.chat_id, f, caption="Daftar Pengguna")
            await m.delete()
        else:
            await m.edit(output_message)

    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/igdl (.+)$'))
async def igdl(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    url = event.pattern_match.group(1)
    m = await event.reply("Mengunduh dari Instagram...")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/d/igdl?url={quote(url)}", timeout=60).json()
        if res.get("status") and res.get("data"):
            media_files = res.get("data", [])
            if not media_files:
                await m.edit("❌ Tidak ada media yang ditemukan di URL tersebut.")
                return

            await m.edit(f"✅ Ditemukan {len(media_files)} media. Mengirim...")

            for i, media in enumerate(media_files):
                media_url = media.get("url")
                if media_url:
                    try:
                        await client.send_file(
                            event.chat_id,
                            file=media_url,
                            caption=f"Media {i+1}/{len(media_files)}",
                            reply_to=event.id
                        )
                    except Exception as e:
                        await event.reply(f"❌ Gagal mengirim media {i+1}: {e}")

            await m.delete() # Hapus pesan "Mengirim..."
        else:
            await m.edit(f"❌ Gagal mengunduh dari Instagram. Pesan dari API: `{res.get('data', 'Tidak ada data')}`")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/cekgroup$'))
async def cek_group(event):
    sender = await event.get_sender()
    if not await is_authorized(sender): return
    m = await event.reply("🔄 Mengambil daftar grup...")
    groups = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                groups.append(f"- {dialog.name} (`{dialog.id}`)")

        if not groups:
            await m.edit("Tidak ada grup yang ditemukan.")
            return

        output_message = "👥 **Daftar Grup:**\n\n" + "\n".join(groups)

        if len(output_message) > 4096:
            await m.edit("Jumlah grup terlalu banyak, mengirim sebagai file...")
            with io.StringIO(output_message) as f:
                f.name = "groups.txt"
                await client.send_file(event.chat_id, f, caption="Daftar Grup")
            await m.delete()
        else:
            await m.edit(output_message)

    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/broadcast(?:\s+(.*))?$', outgoing=True))
async def broadcast(event):
    if not await is_owner(await event.get_sender()): return

    input_str = event.pattern_match.group(1)
    reply_msg = await event.get_reply_message()

    if not input_str and not reply_msg:
        await event.edit("❗️ **Gagal Broadcast**\n\n**Cara Penggunaan:**\n"
                         "1. `/broadcast <pesan> | <id1>,<id2>,...`\n"
                         "2. Balas pesan: `/broadcast <id1>,<id2>,...`\n"
                         "3. Gunakan `all_users` atau `all_groups` sebagai ID target.\n\n"
                         "**Contoh:**\n"
                         "`/broadcast Halo semua | all_users`\n"
                         "`/broadcast Cek pengumuman | 12345678,-10012345678`")
        return

    m = await event.edit("🔄 Memulai proses broadcast...")

    message_to_send = ""
    target_str = ""

    if reply_msg:
        message_to_send = reply_msg
        target_str = input_str
    elif input_str and "|" in input_str:
        parts = input_str.split('|', 1)
        message_to_send = parts[0].strip()
        target_str = parts[1].strip()
    else:
        await m.edit("❗️ Format perintah tidak valid. Gunakan `|` untuk memisahkan pesan dan target.")
        return

    if not target_str:
        await m.edit("❗️ Target broadcast tidak ditentukan.")
        return

    targets = []
    if "all_users" in target_str:
        await m.edit("🔄 Mengambil semua pengguna...")
        async for dialog in client.iter_dialogs():
            if dialog.is_user and not dialog.entity.bot:
                targets.append(dialog.id)
    elif "all_groups" in target_str:
        await m.edit("🔄 Mengambil semua grup...")
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                targets.append(dialog.id)
    else:
        try:
            targets = [int(x.strip()) for x in target_str.split(',')]
        except ValueError:
            await m.edit("❗️ ID Target tidak valid. Harap pisahkan dengan koma.")
            return

    if not targets:
        await m.edit("❗️ Tidak ada target yang valid untuk broadcast.")
        return

    await m.edit(f"🚀 Memulai broadcast ke {len(targets)} chat...")

    # Jika pesan berupa teks, kirim ke diri sendiri dulu agar bisa di-forward
    if isinstance(message_to_send, str):
        try:
            sent_msg = await client.send_message(me.id, message_to_send)
            message_to_send = sent_msg
        except Exception as e:
            await m.edit(f"❌ Gagal mengirim pesan awal untuk diforward: {e}")
            return

    successful_sends = 0
    failed_sends = 0

    for target_id in targets:
        try:
            # Selalu forward pesan untuk menampilkan "Pesan Diteruskan"
            await client.forward_messages(target_id, message_to_send)
            successful_sends += 1
        except Exception:
            failed_sends += 1
        await asyncio.sleep(1.5) # Delay to avoid rate limits

    summary = (f"✅ **Broadcast Selesai**\n\n"
               f"- Berhasil terkirim: {successful_sends}\n"
               f"- Gagal terkirim: {failed_sends}\n"
               f"- Total target: {len(targets)}")

    await m.edit(summary)

@client.on(events.NewMessage(pattern=r'^/ping$'))
async def ping(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    t0 = time.time()
    m = await event.reply("🔄 Checking...")
    ping_ms = (time.time() - t0) * 1000
    txt = (f"🚀 Awan Userbot\n⚡ Ping: {int(ping_ms)} ms\n💻 CPU: {cpu_safe()}\n"
           f"💾 RAM: {psutil.virtual_memory().percent}%\n💽 Disk: {psutil.disk_usage('/').percent}%\n⏳ Uptime: {uptime_str()}")
    await m.edit(txt)

@client.on(events.NewMessage(pattern=r'^/whois(?:\s+(.+))?$'))
async def whois(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    m = await event.reply("🔎 Menganalisis...")
    target = event.pattern_match.group(1)
    try:
        if target:
            t = target.strip()
            if t.isdigit():
                user = await client.get_entity(int(t))
            else:
                user = await client.get_entity(t)
        elif event.is_reply:
            user = (await event.get_reply_message()).sender
        else:
            user = sender
        full = await client(GetFullUserRequest(user.id))
        about = getattr(full, "about", "") or "-"
        username = f"@{user.username}" if getattr(user, "username", None) else "-"
        name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        phone = f"+{user.phone}" if getattr(user, "phone", None) else "Tidak dapat diakses"
        verified = "Ya" if getattr(user, "verified", False) else "Tidak"
        is_bot = "Ya" if getattr(user, "bot", False) else "Tidak"
        status = format_user_status(getattr(user, "status", None))
        profile_photos = await client.get_profile_photos(user, limit=1)
        photo_file = None
        if profile_photos and len(profile_photos) > 0:
            try:
                photo_file = await client.download_media(profile_photos[0], file=bytes)
            except:
                photo_file = None
        first_seen = None
        if not event.is_private:
            first_seen = await find_first_message_date(event.chat_id, user.id, max_messages=20000)
        first_seen_text = first_seen.strftime("%Y-%m-%d %H:%M:%S") if first_seen else "Tidak ditemukan dalam riwayat (atau private)"
        joined_telegram = "Tidak tersedia dari API"
        text = (
            f"👤 Informasi Pengguna\n\n"
            f"Nama: {name}\n"
            f"Username: {username}\n"
            f"User ID: `{user.id}`\n"
            f"No. Telepon: {phone}\n"
            f"Akun Bot: {is_bot}\n"
            f"Terverifikasi: {verified}\n"
            f"Status terakhir: {status}\n"
            f"Bio:\n`{about}`\n\n"
            f"First seen di chat ini: {first_seen_text}\n"
            f"Tanggal bergabung Telegram: {joined_telegram}"
        )
        if photo_file:
            await client.send_file(event.chat_id, io.BytesIO(photo_file), caption=text, reply_to=event.id)
            await m.delete()
            return
        await m.edit(text)
    except Exception as e:
        await m.edit(f"❌ Tidak dapat mengambil info. {e}")

@client.on(events.NewMessage(pattern=r'^/text (.+)$'))
async def text2sticker(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    txt = event.pattern_match.group(1)
    img = Image.new("RGBA", (512,512), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    w,h = draw.textbbox((0,0), txt, font=font)[2:]
    draw.text(((512-w)/2, (512-h)/2), txt, font=font, fill="white")
    out = io.BytesIO()
    out.name = "sticker.webp"
    img.save(out, "WEBP")
    out.seek(0)
    if sender.id == OWNER_ID:
        await event.delete()
    await client.send_file(event.chat_id, out, force_document=False, reply_to=event.id if sender.id!=OWNER_ID else None)

@client.on(events.NewMessage(pattern=r'^/ttsearch (.+)$'))
async def ttsearch(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    q = event.pattern_match.group(1)
    m = await event.reply(f"Mencari TikTok: {q}")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/s/tiktok?query={quote(q)}", timeout=20).json()
        if res.get("status") and res.get("data"):
            info = res["data"][0]
            await client.send_file(event.chat_id, file=info.get("play"), caption=f"{info.get('title')}", reply_to=event.id)
            await m.delete()
        else:
            await m.edit("❌ Tidak ditemukan")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/ytsearch (.+)$'))
async def ytsearch(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    q = event.pattern_match.group(1)
    m = await event.reply(f"Mencari YouTube: {q}")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/s/youtube?query={quote(q)}", timeout=20).json()
        if res.get("status") and res.get("data"):
            videos = [i for i in res["data"] if i.get("type")=="video"][:5]
            if not videos:
                await m.edit("❌ Tidak ada hasil video")
                return
            text = f"Hasil untuk `{q}`:\n\n"
            for v in videos:
                title = v.get("title")
                url = v.get("url")
                channel = v.get("author", {}).get("name","-")
                text += f"{title}\nChannel: {channel}\n{url}\n\n"
            await m.edit(text, link_preview=False)
        else:
            await m.edit("❌ Tidak ada hasil")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/pinterest (.+)$'))
async def pinterest(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    q = event.pattern_match.group(1)
    m = await event.reply(f"Mencari Pinterest: {q}")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/s/pinterest?query={quote(q)}&type=image", timeout=20).json()
        if res.get("status") and res.get("data"):
            info = res["data"][0]
            await client.send_file(event.chat_id, file=info.get("image_url"), caption=info.get("grid_title",""), reply_to=event.id)
            await m.delete()
        else:
            await m.edit("❌ Tidak ditemukan")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/twdl (.+)$'))
async def twdl(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    url = event.pattern_match.group(1)
    m = await event.reply("Mengunduh dari Twitter/X...")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/d/twitter?url={quote(url)}", timeout=60).json()
        if res.get("status") and res.get("data"):
            await client.send_file(event.chat_id, file=res["data"][0].get("url"), caption="✅ Selesai", reply_to=event.id)
            await m.delete()
        else:
            await m.edit("❌ Gagal")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/fbdl (.+)$'))
async def fbdl(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    url = event.pattern_match.group(1)
    m = await event.reply("Mengunduh dari Facebook...")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/d/fb?url={quote(url)}", timeout=60).json()
        if res.get("status") and res.get("data"):
            await client.send_file(event.chat_id, file=res["data"][0].get("url"), caption="✅ Selesai", reply_to=event.id)
            await m.delete()
        else:
            await m.edit("❌ Gagal")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/capcut (.+)$'))
async def capcut(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    url = event.pattern_match.group(1)
    m = await event.reply("Mengunduh template CapCut...")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/d/capcut?url={quote(url)}", timeout=60).json()
        if res.get("status") and res.get("data"):
            await client.send_file(event.chat_id, file=res["data"][0].get("download"), caption="✅ Selesai", reply_to=event.id)
            await m.delete()
        else:
            await m.edit("❌ Gagal")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/scdl (.+)$'))
async def scdl(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    q = event.pattern_match.group(1)
    m = await event.reply("Mencari SoundCloud...")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/s/soundcloud?query={quote(q)}", timeout=30).json()
        if res.get("status") and res.get("data"):
            url = res["data"][0].get("url")
            dl = requests.get(f"https://api.siputzx.my.id/api/d/soundcloud?url={quote(url)}", timeout=60).json()
            if dl.get("status") and dl.get("data"):
                await client.send_file(event.chat_id, file=dl["data"].get("download"), caption="✅ Selesai", reply_to=event.id)
                await m.delete()
                return
        await m.edit("❌ Tidak ditemukan")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/ghdl (.+)$'))
async def ghdl(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    url = event.pattern_match.group(1)
    m = await event.reply("Mengunduh repositori GitHub...")
    try:
        res = requests.get(f"https://api.siputzx.my.id/api/d/github?url={quote(url)}", timeout=60).json()
        if res.get("status") and res.get("data") and "download_url" in res.get("data"):
            download_url = res["data"]["download_url"]
            repo_name = res["data"].get("repo", "repository")

            # Mendownload file
            file_response = requests.get(download_url, stream=True, timeout=300) # Timeout 5 menit
            file_response.raise_for_status()

            # Menyimpan file ke buffer
            file_buffer = io.BytesIO()
            total_downloaded = 0
            for chunk in file_response.iter_content(chunk_size=8192):
                file_buffer.write(chunk)
                total_downloaded += len(chunk)
                # Anda bisa menambahkan progress update di sini jika mau

            file_buffer.seek(0)
            file_buffer.name = f"{repo_name}.zip"

            await client.send_file(
                event.chat_id,
                file=file_buffer,
                caption=f"✅ Repositori `{repo_name}` berhasil diunduh.",
                reply_to=event.id,
                attributes=[DocumentAttributeAudio(duration=0, title=file_buffer.name, performer=None)] # Trik untuk menampilkan nama file
            )
            await m.delete()
        else:
            await m.edit(f"❌ Gagal mengunduh repositori. Pesan dari API: `{res.get('data', 'Tidak ada data')}`")
    except requests.exceptions.Timeout:
        await m.edit("❌ Error: Waktu permintaan habis saat mengunduh file.")
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/topdf$'))
async def topdf(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    if not event.is_reply:
        await event.reply("Reply ke foto/album untuk convert ke PDF")
        return
    msg = await event.get_reply_message()
    photos = []
    if msg.photo:
        photos = [msg]
    elif msg.grouped_id:
        msgs = await client.get_messages(event.chat_id, ids=range(msg.id, msg.id+100))
        photos = [m for m in msgs if m.photo]
    imgs = []
    for m in photos:
        b = await client.download_media(m, file=bytes)
        img = Image.open(io.BytesIO(b)).convert("RGB")
        imgs.append(img)
    if not imgs:
        await event.reply("Tidak ada foto pada pesan reply")
        return
    out = io.BytesIO()
    imgs[0].save(out, format="PDF", save_all=True, append_images=imgs[1:])
    out.name = "images.pdf"
    out.seek(0)
    await client.send_file(event.chat_id, out, caption="📄 PDF", reply_to=event.id)

@client.on(events.NewMessage(pattern=r'^/resize (.+)$'))
async def resize(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    size = event.pattern_match.group(1)
    if "x" not in size or not event.is_reply:
        await event.reply("Gunakan /resize WxH dan reply foto")
        return
    w,h = size.split("x")
    try:
        w,h = int(w), int(h)
    except:
        await event.reply("Ukuran tidak valid")
        return
    msg = await event.get_reply_message()
    if not msg.photo:
        await event.reply("Reply ke foto")
        return
    b = await client.download_media(msg, file=bytes)
    img = Image.open(io.BytesIO(b)).convert("RGBA")
    img = img.resize((w,h), Image.LANCZOS)
    out = io.BytesIO()
    out.name = "resized.png"
    img.save(out, "PNG")
    out.seek(0)
    await client.send_file(event.chat_id, out, reply_to=event.id)

@client.on(events.NewMessage(pattern=r'^/audiotext$'))
async def audiotext(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    if not event.is_reply:
        await event.reply("Reply voice/file audio")
        return
    msg = await event.get_reply_message()
    file = await client.download_media(msg, file=bytes)
    temp_in = "tmp_in_audio"
    with open(temp_in, "wb") as f:
        f.write(file)
    try:
        audio = AudioSegment.from_file(temp_in)
        wav_path = "tmp_audio.wav"
        audio.export(wav_path, format="wav")
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
        await event.reply(f"📝 Hasil:\n{text}")
    except Exception as e:
        await event.reply(f"❌ Gagal: {e}")
    finally:
        for p in [temp_in, "tmp_audio.wav"]:
            if os.path.exists(p): os.remove(p)

@client.on(events.NewMessage(pattern=r'^/setwelcome (.+)$'))
async def setwelcome(event):
    if not await is_owner(await event.get_sender()): return
    txt = event.pattern_match.group(1)
    data = load_data()
    data["welcome"][str(event.chat_id)] = txt
    save_data(data)
    await event.reply("✅ Welcome tersimpan")

@client.on(events.NewMessage(pattern=r'^/anti (on|off)$'))
async def anti_link(event):
    if not await is_owner(await event.get_sender()): return
    v = event.pattern_match.group(1)
    data = load_data()
    data["anti_link"][str(event.chat_id)] = (v=="on")
    save_data(data)
    await event.reply(f"Anti-link set to {v}")

@client.on(events.NewMessage())
async def group_listener(event):
    if event.is_private: return
    data = load_data()
    gid = str(event.chat_id)
    if event.message.action and getattr(event.message.action, "user_id", None):
        try:
            welcome = data["welcome"].get(gid)
            if welcome:
                uid = event.message.action.user_id
                u = await client.get_entity(uid)
                await client.send_message(event.chat_id, welcome.replace("{user}", f"[{u.first_name}](tg://user?id={uid})"), link_preview=False)
        except: pass
    if data["anti_link"].get(gid):
        if event.message.message and ("http://" in event.message.message or "https://" in event.message.message):
            try:
                sender = await event.get_sender()
                if sender and not (await is_owner(sender) or sender.id in data.get("cloned_users", [])):
                    await event.delete()
            except: pass

@client.on(events.NewMessage(pattern=r'^/meme$'))
async def meme(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    m = await event.reply("Mencari meme...")
    try:
        res = requests.get("https://meme-api.herokuapp.com/gimme", timeout=10).json()
        await client.send_file(event.chat_id, res.get("url"), caption=res.get("title"), reply_to=event.id)
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/fancy (.+)$'))
async def fancy(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    txt = event.pattern_match.group(1)
    styles = [
        lambda s: " ".join(list(s)),
        lambda s: "".join(chr(ord(c)+0xFEE0) if 33<=ord(c)<=126 else c for c in s),
        lambda s: "".join(c+"̷" for c in s),
    ]
    out_lines = []
    for style_fn in styles:
        try:
            out_lines.append(style_fn(txt))
        except:
            out_lines.append(txt)
    out = "\n\n".join(out_lines)
    await event.reply(out)

@client.on(events.NewMessage(pattern=r'^/quotes$'))
async def quotes(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    try:
        res = requests.get("https://api.quotable.io/random", timeout=10).json()
        await event.reply(f"“{res.get('content')}” — {res.get('author')}")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/(menfess|confess)\s+([^|]+)\|([^|]+)\|(@\w+)$'))
async def menfess_handler(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return

    try:
        command, message, from_name, to_username = event.pattern_match.groups()
        message = message.strip()
        from_name = from_name.strip()
        to_username = to_username.strip()

        m = await event.reply(f"🔄 Mengirim pesan {command} ke {to_username}...")

        # Dapatkan target user
        try:
            target_user = await client.get_entity(to_username)
        except (ValueError, TypeError):
            await m.edit(f"❌ Username `{to_username}` tidak valid atau tidak ditemukan.")
            return

        # Format pesan
        formatted_message = (
            f"╭─❏「 **PESAN {command.upper()} BARU** 」\n"
            "│\n"
            f"├- 💌 **Pesan:** {message}\n"
            f"├- 🤫 **Dari:** {from_name}\n"
            "│\n"
            "╰─❏\n\n"
            f"_(Pesan ini dikirim melalui userbot. Balas pesan ini dengan `/balas <pesan>` untuk membalas)_"
        )

        # Kirim pesan ke target
        sent_message = await client.send_message(target_user.id, formatted_message)

        # Simpan log untuk fitur balas
        data = load_data()
        menfess_log = data.get("menfess_log", {})
        # Kunci log adalah ID pesan di chat target, valuenya adalah ID pengirim asli
        menfess_log[str(sent_message.id)] = {
            "original_sender_id": sender.id,
            "original_chat_id": event.chat_id,
            "target_user_id": target_user.id
        }
        data["menfess_log"] = menfess_log
        save_data(data)

        await m.edit(f"✅ Pesan {command} berhasil dikirim ke {to_username}.")

    except Exception as e:
        await event.reply(f"❌ Terjadi kesalahan: {e}\n\n**Format yang benar:**\n`/{event.pattern_match.group(1)} pesan|nama samaran|@username`")

@client.on(events.NewMessage(pattern=r'^/balas\s+(.+)'))
async def balas_handler(event):
    if not event.is_reply:
        await event.reply("❗️ Perintah ini harus digunakan dengan membalas pesan menfess/confess.")
        return

    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return

    try:
        reply_message_text = event.pattern_match.group(1).strip()
        reply_to_msg = await event.get_reply_message()
        reply_to_id = str(reply_to_msg.id)

        data = load_data()
        menfess_log = data.get("menfess_log", {})

        if reply_to_id not in menfess_log:
            await event.reply("❗️ Pesan yang Anda balas bukan pesan menfess/confess yang bisa dibalas melalui bot ini.")
            return

        m = await event.reply("🔄 Mengirim balasan...")

        original_sender_id = menfess_log[reply_to_id]["original_sender_id"]

        # Format balasan
        formatted_reply = (
            f"╭─❏「 **BALASAN UNTUKMU** 」\n"
            "│\n"
            f"├- 💬 **Pesan:** {reply_message_text}\n"
            "│\n"
            f"╰─❏\n\n"
            f"_(Ini adalah balasan untuk pesan menfess/confess yang Anda kirim sebelumnya.)_"
        )

        try:
            await client.send_message(original_sender_id, formatted_reply)
            await m.edit("✅ Balasan berhasil dikirim.")
        except Exception as e:
            await m.edit(f"❌ Gagal mengirim balasan ke pengirim asli. Mungkin saya diblokir. Error: {e}")

    except Exception as e:
        await event.reply(f"❌ Terjadi kesalahan saat memproses balasan: {e}")

@client.on(events.NewMessage(pattern=r'^/cekip$'))
async def cekip(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    try:
        ip = requests.get("https://api.ipify.org").text
        geo = requests.get(f"http://ip-api.com/json/{ip}", timeout=10).json()
        txt = f"IP: `{ip}`\nNegara: {geo.get('country')}\nKota: {geo.get('city')}\nISP: {geo.get('isp')}"
        await event.reply(txt)
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/crypto (.+)$'))
async def crypto(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    sym = event.pattern_match.group(1).lower()
    try:
        res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={quote(sym)}&vs_currencies=usd", timeout=10)
        if res.status_code != 200:
            await event.reply("❌ Tidak ditemukan")
            return
        data = res.json()
        if not data:
            await event.reply("❌ Tidak ditemukan")
            return
        usd = list(data.values())[0].get("usd")
        await event.reply(f"{sym.upper()} = ${usd}")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/cuaca (.+)$'))
async def cuaca(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    kota = event.pattern_match.group(1)
    try:
        apikey = os.environ.get("OPENWEATHER_API_KEY", "e3cd2c303e5164b7d10b7bcd0c8160e5")
        res = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={quote(kota)}&appid={apikey}&units=metric&lang=id", timeout=10)
        if res.status_code != 200:
            await event.reply("❌ Gagal mengambil data cuaca. Pastikan nama kota benar dan API Key valid.")
            return
        d = res.json()
        txt = (f"Cuaca di {d['name']}, {d['sys']['country']}\n"
               f"{d['weather'][0]['description'].capitalize()}\n"
               f"Suhu: {d['main']['temp']}°C\nKelembapan: {d['main']['humidity']}%")
        await event.reply(txt)
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/shortlink (.+)$'))
async def shortlink(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    url = event.pattern_match.group(1)
    try:
        res = requests.post("https://cleanuri.com/api/v1/shorten", data={"url": url}, timeout=10).json()
        if res.get("result_url"):
            await event.reply(f"Shortlink: {res['result_url']}")
        else:
            await event.reply("❌ Gagal")
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/github (.+)$'))
async def github(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    username = event.pattern_match.group(1)
    m = await event.reply(f"🔎 Mencari pengguna GitHub `{username}`...")
    try:
        res = requests.get(f"https://api.github.com/users/{quote(username)}", timeout=10).json()
        if res.get("message") == "Not Found":
            await m.edit(f"❌ Pengguna GitHub `{username}` tidak ditemukan.")
            return

        name = res.get('name') or 'Tidak ada nama'
        user_login = res.get('login')
        bio = res.get('bio') or 'Tidak ada bio'
        company = res.get('company') or 'Tidak ada perusahaan'
        location = res.get('location') or 'Tidak ada lokasi'
        blog = res.get('blog') or 'Tidak ada blog'
        followers = res.get('followers', 0)
        following = res.get('following', 0)
        public_repos = res.get('public_repos', 0)
        created_at = res.get('created_at', '').split('T')[0]
        avatar_url = res.get('avatar_url')

        text = (
            f"👤 **Info Pengguna GitHub: {user_login}**\n\n"
            f"**Nama:** {name}\n"
            f"**Bio:** {bio}\n"
            f"**Perusahaan:** {company}\n"
            f"**Lokasi:** {location}\n"
            f"**Blog:** {blog}\n"
            f"**Pengikut:** {followers}\n"
            f"**Mengikuti:** {following}\n"
            f"**Repositori Publik:** {public_repos}\n"
            f"**Bergabung pada:** {created_at}\n"
            f"**Link:** [Buka Profil](https://github.com/{quote(username)})"
        )
        if avatar_url:
            try:
                photo = await client.download_media(avatar_url, file=bytes)
                await client.send_file(event.chat_id, io.BytesIO(photo), caption=text, reply_to=event.id, link_preview=False)
                await m.delete()
                return
            except:
                pass
        await m.edit(text, link_preview=False)
    except Exception as e:
        await m.edit(f"❌ Error: {e}")


@client.on(events.NewMessage(pattern=r'^/botnik(?:\s+(.*))?$'))
async def botnik(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return

    query = event.pattern_match.group(1)
    if not query:
        await event.reply("**Perintah /botnik**\n\n"
                          "Gunakan perintah ini untuk mencari data berdasarkan query.\n"
                          "**Contoh:** `/botnik example@gmail.com`")
        return

    if LEAKOSINT_API_TOKEN == "YOUR_LEAKOSINT_API_TOKEN":
        await event.reply("❗️ `LEAKOSINT_API_TOKEN` belum diatur. Harap edit file `wanz.py` dan atur token Anda.")
        return

    m = await event.reply(f"🔎 Mencari data untuk `{query}`...")

    try:
        data = {
            "token": LEAKOSINT_API_TOKEN,
            "request": query,
            "limit": 300,
            "lang": "en"
        }
        url = 'https://leakosintapi.com/'
        response = await asyncio.to_thread(requests.post, url, json=data, timeout=120)
        response.raise_for_status()
        res_json = response.json()

        if "Error code" in res_json:
            await m.edit(f"❌ API Error: {res_json.get('Error code')}")
            return

        if not res_json.get("List") or not any(res_json["List"].values()):
             await m.edit(f"❌ Tidak ada hasil yang ditemukan untuk `{query}`.")
             return

        report_text = f"**Hasil Pencarian untuk:** `{query}`\n\n"

        results_found = False
        for db_name, db_data in res_json.get("List", {}).items():
            if db_name == "No results found" or not db_data.get("Data"):
                continue

            results_found = True
            report_text += f"**📂 Database:** `{db_name}`\n"
            info_leak = db_data.get("InfoLeak", "")
            if info_leak:
                report_text += f"**ℹ️ Info:** {info_leak}\n"

            report_text += "\n"

            for item in db_data["Data"]:
                for key, value in item.items():
                    report_text += f"  - **{key.replace('_', ' ').title()}:** `{value}`\n"
                report_text += "---\n"

        if not results_found:
             await m.edit(f"❌ Tidak ada hasil yang ditemukan untuk `{query}`.")
             return

        if len(report_text) > 4096:
            await m.edit("`Hasil terlalu panjang, mengirim sebagai file...`")
            with io.BytesIO(report_text.encode('utf-8')) as f:
                f.name = "botnik_results.txt"
                await client.send_file(event.chat_id, f, caption=f"Hasil pencarian untuk `{query}`.", reply_to=event.id)
            await m.delete()
        else:
            await m.edit(report_text, link_preview=False)

    except requests.exceptions.Timeout:
        await m.edit("❌ Error: Permintaan ke API timeout.")
    except requests.exceptions.RequestException as e:
        await m.edit(f"❌ Error Koneksi: {e}")
    except Exception as e:
        await m.edit(f"❌ Terjadi kesalahan tak terduga: {e}")


@client.on(events.NewMessage(pattern=r'^/tr ([\w-]+) (.+)'))
async def translate(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    to_lang = event.pattern_match.group(1)
    text = event.pattern_match.group(2)
    m = await event.reply("🔄 Menerjemahkan...")
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={to_lang}&dt=t&q={quote(text)}"
        res = requests.get(url, timeout=10).json()
        translated_text = res[0][0][0]
        from_lang = res[2]
        await m.edit(f"**Diterjemahkan dari `{from_lang}` ke `{to_lang}`:**\n\n{translated_text}")
    except Exception as e:
        await m.edit(f"❌ Gagal menerjemahkan: {e}")

@client.on(events.NewMessage(pattern=r'^/ud (.+)$'))
async def urban_dictionary(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return
    term = event.pattern_match.group(1)
    m = await event.reply(f"🔎 Mencari `{term}` di Urban Dictionary...")
    try:
        res = requests.get(f"https://api.urbandictionary.com/v0/define?term={quote(term)}", timeout=10).json()
        if not res or not res.get("list"):
            await m.edit(f"❌ Tidak ada definisi untuk `{term}`.")
            return

        definition = res['list'][0]
        word = definition.get('word')
        meaning = definition.get('definition').replace('[', '').replace(']', '')
        example = definition.get('example').replace('[', '').replace(']', '')

        text = (
            f"**Definisi untuk `{word}`:**\n\n"
            f"**Arti:**\n{meaning}\n\n"
            f"**Contoh:**\n_{example}_"
        )
        await m.edit(text)
    except Exception as e:
        await m.edit(f"❌ Error: {e}")

@client.on(events.NewMessage(pattern=r'^/createweb$'))
async def start_create_web(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return

    user_interaction_state[sender.id] = "awaiting_web_description"

    await event.reply("✅ Siap! Silakan jelaskan situs web seperti apa yang Anda inginkan di pesan berikutnya.")

async def generate_website_code_gemini(prompt: str):
    """Calls the Google Gemini API to generate website code."""
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return None, "Gemini API Key belum diatur. Silakan edit file wanz.py dan atur GEMINI_API_KEY."

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': GEMINI_API_KEY
    }

    # Adding more specific instructions for HTML structure
    full_prompt = f"Generate a single, complete HTML file based on the following description: '{prompt}'. The HTML file must include all necessary CSS and JavaScript within the same file. The structure should be `<!DOCTYPE html><html><head>...</head><body>...</body></html>`. Ensure the code is complete and ready to be saved as an `index.html` file."

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash/generateContent"

    try:
        response = await asyncio.to_thread(requests.post, url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()

        if 'candidates' in result and result['candidates']:
            generated_code = result['candidates'][0]['content']['parts'][0]['text']
            # Clean the code from markdown
            if generated_code.strip().startswith("```html"):
                generated_code = generated_code.strip()[7:]
                if generated_code.endswith("```"):
                    generated_code = generated_code[:-3]
            return generated_code, None
        elif 'error' in result:
             return None, f"Gagal menghasilkan kode: {result['error'].get('message', 'Error tidak diketahui dari Google AI')}"
        else:
            return None, "Gagal mendapatkan kode dari API. Respon tidak valid atau kosong."

    except requests.exceptions.RequestException as e:
        return None, f"Error koneksi ke Google AI: {e}"
    except Exception as e:
        return None, f"Terjadi error: {e}"

async def loading_animation(message):
    """Animates a loading message."""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    while True:
        try:
            for char in chars:
                await message.edit(f"⏳ Sedang membuat... {char}")
                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            # Task was cancelled, break the loop
            break
        except Exception:
            # Other exceptions (e.g., message deleted)
            break

@client.on(events.NewMessage(func=lambda e: e.sender_id in user_interaction_state and user_interaction_state[e.sender_id] == "awaiting_web_description"))
async def handle_web_description(event):
    sender = await event.get_sender()
    description = event.message.text

    if description.startswith('/'):
        del user_interaction_state[sender.id]
        await event.reply("❌ Pembuatan situs web dibatalkan.")
        return

    del user_interaction_state[sender.id]

    m = await event.reply("⏳ Sedang membuat...")

    loading_task = asyncio.create_task(loading_animation(m))

    code, error = await generate_website_code_gemini(description)

    loading_task.cancel()

    if error:
        await m.edit(f"❌ Terjadi kesalahan: {error}")
        return

    # Clean the generated code
    if code.strip().startswith("```html"):
        code = code.strip()[7:]
        if code.endswith("```"):
            code = code[:-3]

    # Save the code to a file
    file_path = "index.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    await m.edit(f"✅ Kode berhasil dibuat dan disimpan sebagai `{file_path}`. Mengirim file...")

    try:
        await client.send_file(
            event.chat_id,
            file_path,
            caption=f"Berikut adalah situs web yang dibuat berdasarkan deskripsi Anda:\n\n`{description}`",
            reply_to=event.id
        )
        await m.delete()
    except Exception as e:
        await m.edit(f"❌ Gagal mengirim file: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)



@client.on(events.NewMessage(pattern=r'^/group$'))
async def handle_group_menu(event):
    sender = await event.get_sender()
    if not mode_public and not await is_authorized(sender): return

    menu_text = (
        "**⚜️ Menu Manajemen Grup ⚜️**\n\n"
        "Berikut adalah perintah yang tersedia untuk manajemen grup:\n\n"
        " - `/setwelcome <teks>`: Mengatur pesan selamat datang.\n"
        " - `/anti <on/off>`: Mengaktifkan/menonaktifkan anti-link.\n"
        " - `/kick <@user/reply>`: Mengeluarkan anggota dari grup.\n"
    )

    await event.reply(menu_text, link_preview=False)


@client.on(events.NewMessage(pattern=r'^/kick(?: (.*))?$'))
async def kick_user(event):
    if event.is_private:
        await event.reply("❌ Perintah ini hanya bisa digunakan di grup.")
        return

    sender = await event.get_sender()
    if not await is_authorized(sender): return

    try:
        perms = await client.get_permissions(event.chat_id, me.id)
        if not perms.ban_users:
            await event.reply("❗️ Saya tidak punya izin untuk menendang pengguna di sini.")
            return
    except:
        await event.reply("❗️ Gagal memeriksa izin admin.")
        return

    target_user = await get_target_user(event)
    if not target_user:
        await event.reply("❗️ Pengguna tidak ditemukan. Balas pesan pengguna atau berikan username/ID.")
        return

    if target_user.id == me.id:
        await event.reply("😂 Saya tidak bisa menendang diri sendiri.")
        return

    try:
        await client.kick_participant(event.chat_id, target_user.id)
        await event.reply(f"✅ Pengguna {target_user.first_name} (`{target_user.id}`) telah ditendang dari grup.")
    except Exception as e:
        await event.reply(f"❌ Gagal menendang pengguna: {e}")


# --- Fitur Pelacak ---
user_states = {}
LOG_FILE = "message_log.txt"

@client.on(events.NewMessage(pattern=r'^/trackmsg (on|off)$', outgoing=True))
async def toggle_message_tracker(event):
    if not await is_owner(await event.get_sender()):
        return

    action = event.pattern_match.group(1).lower()
    data = load_data()
    is_enabled = (action == "on")
    data['message_tracker_enabled'] = is_enabled
    save_data(data)

    status = "diaktifkan" if is_enabled else "dinonaktifkan"
    await event.edit(f"`✅ Pelacak pesan grup telah {status}.`")

@client.on(events.UserUpdate)
async def user_update_handler(event):
    if not me:
        return

    user_id = event.user_id
    try:
        new_user = await client.get_entity(user_id)
    except:
        return # Gagal mendapatkan info user, mungkin user tidak terjangkau

    old_user_info = user_states.get(user_id)

    current_user_info = {
        'username': new_user.username,
        'first_name': new_user.first_name,
        'last_name': new_user.last_name
    }
    user_states[user_id] = current_user_info

    if not old_user_info:
        return

    changes = []
    if old_user_info['username'] != new_user.username:
        changes.append(f"Username: `{old_user_info['username']}` → `{new_user.username}`")
    if old_user_info['first_name'] != new_user.first_name:
        changes.append(f"Nama Depan: `{old_user_info['first_name']}` → `{new_user.first_name}`")
    if old_user_info['last_name'] != new_user.last_name:
        changes.append(f"Nama Belakang: `{old_user_info['last_name']}` → `{new_user.last_name}`")

    if changes:
        message = (
            f"**⚠️ Perubahan Info Pengguna Terdeteksi**\n\n"
            f"**Pengguna:** [{new_user.first_name}](tg://user?id={user_id})\n"
            f"**ID:** `{user_id}`\n\n"
            "**Perubahan:**\n" + "\n".join(changes)
        )
        try:
            await client.send_message(me.id, message)
        except:
            pass

@client.on(events.NewMessage(incoming=True, func=lambda e: not e.is_private))
async def message_logger(event):
    data = load_data()
    if not data.get('message_tracker_enabled', False):
        return

    try:
        sender = await event.get_sender()
        chat = await event.get_chat()

        if not sender or not chat:
            return

        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
        log_message = (
            f"[{event.date.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"[{chat.title} ({chat.id})] "
            f"{sender_name} ({sender.id}): "
            f"{event.text or '(Pesan non-teks)'}\n"
        )

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception:
        # Menghindari crash jika ada error saat logging
        pass

# --- Akhir Fitur Pelacak ---

@client.on(events.NewMessage(pattern=r'^/eval(?:\s+([\s\S]+))?$', outgoing=True))
async def evaluate(event):
    if not await is_owner(await event.get_sender()):
        return

    code = event.pattern_match.group(1)
    if not code:
        await event.edit("`Berikan kode untuk dieksekusi.`")
        return

    m = await event.edit("`Mengeksekusi...`")

    # Store old stdout and stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()

    try:
        # If the code starts with '!', treat it as a shell command
        if code.strip().startswith("!"):
            command = code.strip()[1:]
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            result = stdout.decode().strip()
            error = stderr.decode().strip()
        else:
            # Prepare the async function to be executed
            exec_code = f'async def __ex(event, client):\n    ' + '\n    '.join(code.split('\n'))

            # Execute the code
            exec(exec_code, globals(), locals())

            # Call the async function
            result_obj = await locals()['__ex'](event, client)
            result = str(result_obj) if result_obj is not None else ""

            # Get output from stdout
            output = redirected_output.getvalue().strip()
            if output:
                result = output if not result else f"{result}\n{output}"

            error = redirected_error.getvalue().strip()

    except Exception:
        error = traceback.format_exc()
        result = ""
    finally:
        # Restore stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    # Format the output message
    output_message = ""
    if result:
        output_message += f"**✅ HASIL:**\n```{result}```\n"
    if error:
        output_message += f"**❌ ERROR:**\n```{error}```\n"

    if not output_message:
        output_message = "`Eksekusi selesai tanpa output.`"

    # Send the output
    if len(output_message) > 4096:
        with io.BytesIO(output_message.encode()) as f:
            f.name = "eval_output.txt"
            await m.edit("`Output terlalu panjang, mengirim sebagai file.`")
            await client.send_file(event.chat_id, f, caption="Hasil Eksekusi")
    else:
        await m.edit(output_message)


async def check_username(username, site_url_format):
    """Asynchronously checks if a username exists on a given site."""
    url = site_url_format.format(username=username)
    try:
        # Use asyncio.to_thread to run the blocking requests.get in a separate thread
        response = await asyncio.to_thread(requests.get, url, timeout=5)
        if response.status_code == 200:
            return url
    except requests.exceptions.RequestException:
        pass
    return None

@client.on(events.NewMessage(pattern=r'^/osint(?:\s+(.+))?$'))
async def osint(event):
    if not await is_owner(await event.get_sender()):
        return

    m = await event.reply("`🔎 Melakukan penyelidikan OSINT...`")

    target_user = await get_target_user(event)
    if not target_user:
        await m.edit("`❗️ Pengguna tidak ditemukan. Balas pesan atau berikan username/ID.`")
        return

    # 1. Get Telegram Info
    try:
        full = await client(GetFullUserRequest(target_user.id))
        about = getattr(full, "about", "") or "-"
        username = f"@{target_user.username}" if getattr(target_user, "username", None) else "Tidak ada"
        name = f"{target_user.first_name or ''} {target_user.last_name or ''}".strip()

        info_text = (
            f"**👤 Informasi Dasar Telegram**\n\n"
            f"**Nama:** {name}\n"
            f"**Username:** {username}\n"
            f"**User ID:** `{target_user.id}`\n"
            f"**Bio:** `{about}`\n\n"
            f"**Disclaimer:** Informasi di bawah ini adalah hasil pencarian otomatis berdasarkan username dan mungkin tidak akurat."
        )
    except Exception as e:
        await m.edit(f"`❌ Gagal mendapatkan info Telegram: {e}`")
        return

    # 2. Check username on other platforms
    if not target_user.username:
        await m.edit(info_text + "\n\n`Tidak ada username untuk dicari di platform lain.`")
        return

    await m.edit(info_text + "\n\n`🕵️‍♂️ Mencari username di platform lain...`")

    sites_to_check = {
        "GitHub": "https://github.com/{username}",
        "Twitter/X": "https://twitter.com/{username}",
        "Instagram": "https://www.instagram.com/{username}",
        "TikTok": "https://www.tiktok.com/@{username}",
        "Reddit": "https://www.reddit.com/user/{username}",
        "Pinterest": "https://www.pinterest.com/{username}/",
    }

    tasks = [check_username(target_user.username, url_format) for url_format in sites_to_check.values()]
    results = await asyncio.gather(*tasks)

    found_sites = []
    site_names = list(sites_to_check.keys())
    for i, url in enumerate(results):
        if url:
            found_sites.append(f"- [{site_names[i]}]({url})")

    if found_sites:
        found_text = "\n\n**🌐 Profil Ditemukan di Platform Lain:**\n" + "\n".join(found_sites)
    else:
        found_text = "\n\n`Tidak ada profil yang ditemukan di platform lain dengan username ini.`"

    final_output = info_text + found_text
    await m.edit(final_output, link_preview=False)


async def main():
    global me
    load_afk_from_disk()
    await client.start()
    me = await client.get_me()
    print(f"🔥 Userbot berjalan sebagai {me.first_name}...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.loop.run_until_complete(main())
