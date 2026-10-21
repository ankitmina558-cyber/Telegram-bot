
import asyncio
import logging
import sqlite3
import re

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CopyTextButton,
)
from telegram.error import Forbidden, RetryAfter
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =====================================================
# BOT SETTINGS
# =====================================================

TOKEN = "bot_token"
ADMIN_IDS = {123456789}

CHANNEL_ID = "@stylishnamemaker"
CHANNEL_URL = "https://t.me/stylishnamemaker"

DB_NAME = "bot_users.db"
HISTORY_LIMIT = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# =====================================================
# DESIGN TEMPLATES
#
# Use {name} wherever the submitted name should appear.
# Keep your original decorative symbols unchanged.
# =====================================================

DESIGNS = {
    "premium": [
        "🝐꯭𐏓꯭꯭ ⃪🤍𝄄𝄀꯭𝄄꯭ ‌⃪{name} 𝅥‌꯭𝆬‌🍫 𝅥‌꯭𝆬‌ ⃪𝄄𝄀꯭𝄄꯭⎯‌꯭⟶⋆",
        "⎯᪵⎯꯭‌❃⃪꯭‌{name}꯭᪵𝆺꯭𝅥᪵⎯꯭‌⎯꯭💎",
        "𝆺꯭𝅥◄❥‌‌⃟⃝🥀⛦⃕‌ {name}⛦⃕‌❍𝆭𝐏─𝄄꯭꯭𝄄꯭꯭ 𝅥‌꯭𝆬‌🪷",
        "⎯꯭꯭֯‌ ⃪꯭⃛𝂍⃨⃜{name}꯭ ꯭⃜🚬⃪⃜𝅃꯭᳚༎‌꯭꯭➛",
        "𝁘 ໍ {name} 🤍⤹ 𓆪𓂃𔘓",
        "𓆩꯭〬ᬊ꯭{name}𝄢꯭‌‌⃪➤⃝꯭🍷꯭𔘓꯭⃭𝘅꯭𝗗꯭𓆪꯭ꪾ",
        "⎯᪵𓆩〭〬{name}𓆪ᮀ⎯꯭‌ꭗ‌‌➛",
        "⎯꯭‌𓆩꯭{name}𓆪꯭〝‌ ˈˈ‌🌜‌",
        "🦋✨{name}✨🦋",
        "💓{name}:)",
        "𓂃 ࣪˖ ִֶָ {name} 🎀",
        "⌁{name}༎‌꯭",
        "•𝁘ໍ𓈒𝀚‌🦚⃝⃪{name}𓆪ꪾˎ𓂃ֶꪳ",
        "⏤‌‌‌‌{name}‌Ꭼ𝚴Ѻ™🐉",
    ],

    "aesthetic": [
        "⎯꯭‌🤍⃝〭𝆭〬{name} -꯭᪵ᥫ꯭᭡𓂃꯭ ,",
        "ꞋꞌꞋ{name} 🎀 𓄹",
        "𝀚𝆭‌ꪳ{name}🦋𝅯‌𓂃",
        "⎯᪵⎯𐎓⃝꯭꯭🌷꯭ ⃪꯭{name}𝄄꯭𝆺꯭꯭𝆭💗",
        "⤹⌯ {name}⤹°𝅯⃮𖹭᷎᷉",
        "⎯⎯‌꯭꯭{name} ꯭🌷",
        "꯭𝆭𝆭‌‌{name}𝆭 ⃝꯭𝆹𝅥‌‌☜꯭",
        "🌷꧍{name}𔘓‌𝆟🫧𓂃ꪸ𝆔.",
        "✧⃝꯭✨𓆩{name}𓆪✨⃝꯭✧ °🦋°",
        "ㅤㅤ⏤ {name} 🤍",
        "••ᯓ❥ {name} ‹‹/𝟑",
        "🌙꯭𓆩꯭{name}𓆪꯭🌙 °👼🏻°",
        "🪷𐬹𓍼 {name} 𓍢ִ໋🪷",
        "🦅👑꯭{name}꯭👑🦅 𝂈✨",
        "🌸⃝〬𓆩 {name} 𓆪⃝〬🌸 𝂈🤍",
    ],

    "fancy": [
        "𝐍𝐀𝐌𝐄 𝐌𝐀𝐊𝐄𝐑 𝐁𝐎𝐓 ♥🥀:\n{name}",
        "⎯᪵⎯⎯᪶᳚𓆩᪶𝆅{name}𖾓ᷱ᪳𑩖𝂨",
        "⋆⎯⃪{name}𖾓ᷱ᪳𝁛",
        "𝂃{name}𝞃",
        "𝀚᧘{name}𝁛゙˳ ໋",
        "⎯ٜ𝅃⃪᳚🎨ꤦꤦꤦٜ ⃪⃝{name}•⃪ꤦꤦٜ᭡ᰪ𓂃",
        "⎯ ⃪💝⃪{name}⃪𝆅",
        "⋆𝁘ໍ🍥ꠦꠋ{name}𔓎᪳𔓗๋𓂃",
        "𝁘〬᧘{name}𝁜๎",
        "|𝆺𝅥𝆭⋆{name}𝆺𝅥.🫀",
        "⎯𝅃᳚♥️ ⃪⃝{name}•᭡𝆭ᥫ᭡゙𓂃",
        "🤍⃝⃪᪲🩷⃖{name}🌸᪵᪳᪳𝆺𝅥𝆬⎯⟶᯦",
        "⎯࣮ໍ𝁘゙ฺ𝆆{name}👒⃪𝁛ࣰ໋",
        "⎯ࣲ⎯ꪷ꯬៱{name}⎯𐚁𝆆𝁛𝆥",
        "𝁑𝁠{name}𝇄𝆆🦩𝁜",
        "𓆩⃪〭〬🍭⃪⃕⃔ໍ{name}💕𝆭⎯⎯𝁤",
        "𓆩֪ۤ{name}᭧",
        "⃪⃛ ៱{name}𓂃𝆊᪽🐼",
        "•{name}🖤",
        "⟶‌‌𓆩〭〬༲🥃{name} ༎ࠫ🖤",
        "🌸⃝⃘⃜{name}♡︎〭〬𓆪⟶",
        "🎬-★𓆩⃝{name}𓆪★-🛍",
        "⟶‌‌𓆩〭〬༲🥃 {name} ༎ࠫ🖤⟵‌",
        "𝁎🕷⃟⃪ {name} 🕸️˵𝁛",
        "𝁘𝂅⬎‌‌{name}🤍⬎‌",
        "🐼꯭🧋⃝⃨⃜ {name} 🧋꯭⃝⃨⃜🐼",
    ],
}

CATEGORY_NAMES = {
    "premium": "👑 Premium Design",
    "aesthetic": "🌷 Aesthetic Design",
    "fancy": "✨ Fancy Design",
}


# =====================================================
# DATABASE
# =====================================================

def db_connect():
    return sqlite3.connect(DB_NAME, timeout=15)


def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                design TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, design)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                design TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_user(uid):
    with db_connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
            (uid,),
        )


def get_users():
    with db_connect() as conn:
        return [
            row[0] for row in conn.execute(
                "SELECT user_id FROM users"
            ).fetchall()
        ]


def remove_user(uid):
    with db_connect() as conn:
        conn.execute("DELETE FROM users WHERE user_id=?", (uid,))


def save_favorite(uid, design):
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO favorites(user_id, design) "
            "VALUES (?, ?)",
            (uid, design),
        )
        return cursor.rowcount > 0


def get_favorites(uid):
    with db_connect() as conn:
        return [
            row[0] for row in conn.execute(
                "SELECT design FROM favorites "
                "WHERE user_id=? ORDER BY id DESC",
                (uid,),
            ).fetchall()
        ]


def delete_favorite(uid, design):
    with db_connect() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE user_id=? AND design=?",
            (uid, design),
        )


def save_history(uid, name, category, design):
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO history(user_id,name,category,design) "
            "VALUES (?, ?, ?, ?)",
            (uid, name, category, design),
        )


def get_history(uid):
    with db_connect() as conn:
        return conn.execute(
            "SELECT name, category, design, created_at FROM history "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (uid, HISTORY_LIMIT),
        ).fetchall()


def get_stats():
    with db_connect() as conn:
        return tuple(
            conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in ("users", "favorites", "history")
        )


# =====================================================
# CHANNEL MEMBERSHIP
# =====================================================

async def is_joined(uid, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, uid)

        return (
            member.status in ("member", "administrator", "creator")
            or (
                member.status == "restricted"
                and getattr(member, "is_member", False)
            )
        )

    except Exception:
        logger.exception("Membership check failed")
        return False


def join_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Join Channel",
                url=CHANNEL_URL,
            )
        ],
        [
            InlineKeyboardButton(
                "✅ I've Joined",
                callback_data="check_join",
            )
        ],
    ])


async def ask_to_join(message):
    await message.reply_text(
        "🔒 Please join our channel first, then tap "
        "\"I've Joined\" to continue.",
        reply_markup=join_keyboard(),
    )


async def require_membership(update, context):
    user = update.effective_user

    if user and await is_joined(user.id, context):
        return True

    if update.effective_message:
        await ask_to_join(update.effective_message)

    return False


# =====================================================
# MENUS
# =====================================================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👑 Premium Design",
                callback_data="cat:premium",
            )
        ],
        [
            InlineKeyboardButton(
                "🌷 Aesthetic Design",
                callback_data="cat:aesthetic",
            )
        ],
        [
            InlineKeyboardButton(
                "✨ Fancy Design",
                callback_data="cat:fancy",
            )
        ],
        [
            InlineKeyboardButton(
                "⭐ Favorites",
                callback_data="show:favorites",
            ),
            InlineKeyboardButton(
                "🕘 History",
                callback_data="show:history",
            ),
        ],
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin:stats",
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Broadcast",
                callback_data="admin:broadcast",
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Close",
                callback_data="admin:close",
            )
        ],
    ])


# =====================================================
# NAME CONVERSION
# =====================================================

# Recognized spellings of the example name in old templates.
# New templates should use {name} directly.
OLD_NAME_PATTERNS = [
    r"\{NAME\}",
    r"\{name\}",
    r"NAME_PLACEHOLDER",
    r"ANKIT",
    r"Ankit",
    r"ankit",
    r"𝖆𝖓𝖐𝖎𝖙",
    r"𝐀𝐍𝐊𝐈𝐓",
    r"𝐚𝐧𝐤𝐢𝐭",
    r"𝚨꯭𝛈꯭𝐤꯭𝛊꯭τ",
]


def make_design(template, name):
    """
    Replace explicit placeholders and recognizable ANKIT spellings.
    If no sample name exists, append the requested name.
    """

    if "{name}" in template or "{NAME}" in template:
        return (
            template
            .replace("{name}", name)
            .replace("{NAME}", name)
        )

    for pattern in OLD_NAME_PATTERNS[2:]:
        updated, count = re.subn(
            pattern,
            lambda match: name,
            template,
            flags=re.IGNORECASE,
        )
        if count:
            return updated

    # A template without a recognizable sample name still works.
    return f"{template}\n{name}"


# =====================================================
# DESIGN DELIVERY
# =====================================================

async def send_designs(message, context, uid, category):
    name = context.user_data.get("user_name", "")

    if not name:
        context.user_data["waiting_for_name"] = True
        await message.reply_text(
            "Please send your name first."
        )
        return

    templates = DESIGNS[category]
    generated = [
        make_design(template, name)
        for template in templates
    ]

    context.user_data["current_designs"] = generated
    context.user_data["current_category"] = category

    await message.reply_text(
        f"{CATEGORY_NAMES[category]}\n"
        f"Name: {name}\n"
        f"Total designs: {len(generated)}"
    )

    for index, design in enumerate(generated):
        save_history(uid, name, category, design)

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📋 Copy",
                copy_text=CopyTextButton(text=design),
            ),
            InlineKeyboardButton(
                "⭐ Save",
                callback_data=f"fav:add:{index}",
            ),
        ]])

        await message.reply_text(
            design,
            reply_markup=keyboard,
        )


# =====================================================
# START AND NAME INPUT
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_membership(update, context):
        return

    save_user(update.effective_user.id)
    context.user_data["waiting_for_name"] = True
    context.user_data.pop("user_name", None)

    await update.effective_message.reply_text(
        "✨ Welcome to Name Maker Bot!\n\n"
        "Please send the name you want to style."
    )


async def receive_name(update, context):
    user = update.effective_user
    message = update.effective_message

    if not user or not message or not message.text:
        return

    if context.user_data.get("waiting_for_broadcast"):
        return

    if not await require_membership(update, context):
        return

    name = message.text.strip()

    if not name:
        await message.reply_text("Please send a valid name.")
        return

    if len(name) > 50:
        await message.reply_text(
            "Please send a name with 50 characters or fewer."
        )
        return

    context.user_data["user_name"] = name
    context.user_data["waiting_for_name"] = False

    save_user(user.id)

    await message.reply_text(
        f"Name received: {name}\n\n"
        "Please choose a design category:",
        reply_markup=main_menu(),
    )


async def menu_command(update, context):
    if not await require_membership(update, context):
        return

    await update.effective_message.reply_text(
        "🏠 Main Menu",
        reply_markup=main_menu(),
    )


async def help_command(update, context):
    if not await require_membership(update, context):
        return

    await update.effective_message.reply_text(
        "/start - Start the bot\n"
        "/menu - Open the main menu\n"
        "/favorites - View saved designs\n"
        "/history - View recent designs\n"
        "/admin - Open the admin panel"
    )


# =====================================================
# CATEGORY CALLBACK
# =====================================================

async def category_callback(update, context):
    query = update.callback_query
    await query.answer()

    if not await is_joined(query.from_user.id, context):
        await ask_to_join(query.message)
        return

    category = query.data.split(":", 1)[1]

    if category not in DESIGNS:
        await query.message.reply_text("Invalid category.")
        return

    if not context.user_data.get("user_name"):
        context.user_data["waiting_for_name"] = True
        await query.message.reply_text(
            "Please send your name first."
        )
        return

    save_user(query.from_user.id)

    await send_designs(
        query.message,
        context,
        query.from_user.id,
        category,
    )


# =====================================================
# FAVORITES
# =====================================================

async def favorite_callback(update, context):
    query = update.callback_query

    if not await is_joined(query.from_user.id, context):
        await query.answer()
        await ask_to_join(query.message)
        return

    parts = query.data.split(":", 2)

    try:
        index = int(parts[2])
        designs = context.user_data["current_designs"]
        design = designs[index]

    except (ValueError, IndexError, KeyError):
        await query.answer(
            "Session expired. Please open the category again.",
            show_alert=True,
        )
        return

    if parts[1] == "add":
        added = save_favorite(query.from_user.id, design)

        await query.answer(
            "⭐ Saved!" if added else "Already saved."
        )
    else:
        await query.answer("Invalid action.", show_alert=True)


async def show_favorites_message(message, uid):
    favorites = get_favorites(uid)

    if not favorites:
        await message.reply_text("⭐ No saved favorites yet.")
        return

    for index, design in enumerate(favorites):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📋 Copy",
                copy_text=CopyTextButton(text=design),
            ),
            InlineKeyboardButton(
                "🗑 Remove",
                callback_data=f"favlist:remove:{index}",
            ),
        ]])

        await message.reply_text(
            design,
            reply_markup=keyboard,
        )


async def favorite_list_callback(update, context):
    query = update.callback_query

    if not await is_joined(query.from_user.id, context):
        await query.answer()
        await ask_to_join(query.message)
        return

    parts = query.data.split(":")

    try:
        index = int(parts[2])
        favorites = get_favorites(query.from_user.id)
        design = favorites[index]

    except (ValueError, IndexError):
        await query.answer(
            "Please reopen your favorites list.",
            show_alert=True,
        )
        return

    delete_favorite(query.from_user.id, design)

    await query.answer("Removed.")
    await query.message.reply_text("🗑 Favorite removed.")


async def favorites_command(update, context):
    if not await require_membership(update, context):
        return

    await show_favorites_message(
        update.effective_message,
        update.effective_user.id,
    )


# =====================================================
# HISTORY
# =====================================================

async def send_history(message, uid):
    rows = get_history(uid)

    if not rows:
        await message.reply_text("🕘 Your history is empty.")
        return

    for name, category, design, created_at in rows:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "📋 Copy",
                copy_text=CopyTextButton(text=design),
            )
        ]])

        await message.reply_text(
            f"{design}\n"
            f"Category: {CATEGORY_NAMES.get(category, category)}\n"
            f"Date: {created_at}",
            reply_markup=keyboard,
        )


async def history_command(update, context):
    if not await require_membership(update, context):
        return

    await send_history(
        update.effective_message,
        update.effective_user.id,
    )


async def show_callback(update, context):
    query = update.callback_query
    await query.answer()

    if not await is_joined(query.from_user.id, context):
        await ask_to_join(query.message)
        return

    kind = query.data.split(":", 1)[1]

    if kind == "favorites":
        await show_favorites_message(
            query.message,
            query.from_user.id,
        )

    elif kind == "history":
        await send_history(
            query.message,
            query.from_user.id,
        )


# =====================================================
# ADMIN
# =====================================================

def is_admin(uid):
    return uid in ADMIN_IDS


async def admin_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "⛔ Admin only."
        )
        return

    await update.effective_message.reply_text(
        "🛠 Admin Panel",
        reply_markup=admin_menu(),
    )


async def admin_callback(update, context):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("Admin only.", show_alert=True)
        return

    await query.answer()

    action = query.data.split(":", 1)[1]

    if action == "stats":
        users, favorites, history = get_stats()

        await query.message.reply_text(
            "📊 Statistics\n\n"
            f"Users: {users}\n"
            f"Favorites: {favorites}\n"
            f"History: {history}"
        )

    elif action == "broadcast":
        context.user_data["waiting_for_broadcast"] = True

        await query.message.reply_text(
            "Send the broadcast message. "
            "Cancel: /cancelbroadcast"
        )

    elif action == "close":
        await query.edit_message_text(
            "Admin panel closed."
        )


# =====================================================
# BROADCAST
# =====================================================

async def broadcast_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.effective_message.reply_text(
            "⛔ Admin only."
        )
        return

    context.user_data["waiting_for_broadcast"] = True

    await update.effective_message.reply_text(
        "Send the broadcast message. "
        "Cancel: /cancelbroadcast"
    )


async def cancel_broadcast(update, context):
    if not is_admin(update.effective_user.id):
        return

    context.user_data["waiting_for_broadcast"] = False

    await update.effective_message.reply_text(
        "❌ Broadcast cancelled."
    )


async def broadcast_message(update, context):
    user = update.effective_user
    message = update.effective_message

    if not user or not is_admin(user.id):
        return

    if not context.user_data.get("waiting_for_broadcast"):
        return

    if not message or (
        message.text and message.text.startswith("/")
    ):
        return

    context.user_data["waiting_for_broadcast"] = False

    users = get_users()
    success = 0
    failed = 0
    removed = 0

    status = await message.reply_text(
        f"⏳ Broadcast started: {len(users)} users"
    )

    for uid in users:
        try:
            await message.copy(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)

        except RetryAfter as exc:
            delay = exc.retry_after

            if hasattr(delay, "total_seconds"):
                delay = delay.total_seconds()

            await asyncio.sleep(float(delay) + 1)

            try:
                await message.copy(chat_id=uid)
                success += 1

            except Forbidden:
                failed += 1
                removed += 1
                remove_user(uid)

            except Exception:
                failed += 1
                logger.exception("Broadcast retry failed")

        except Forbidden:
            failed += 1
            removed += 1
            remove_user(uid)

        except Exception:
            failed += 1
            logger.exception("Broadcast failed")

    await status.edit_text(
        "✅ Broadcast complete\n\n"
        f"Total: {len(users)}\n"
        f"Success: {success}\n"
        f"Failed: {failed}\n"
        f"Removed: {removed}"
    )

    raise ApplicationHandlerStop


# =====================================================
# CHANNEL JOIN VERIFICATION
# =====================================================

async def check_join_callback(update, context):
    query = update.callback_query
    await query.answer()

    if not await is_joined(query.from_user.id, context):
        await ask_to_join(query.message)
        return

    save_user(query.from_user.id)

    context.user_data["waiting_for_name"] = True

    await query.message.reply_text(
        "✅ Membership verified!\n\n"
        "Please send the name you want to style."
    )


async def menu_callback(update, context):
    query = update.callback_query
    await query.answer()

    if not await is_joined(query.from_user.id, context):
        await ask_to_join(query.message)
        return

    await query.message.reply_text(
        "🏠 Main Menu",
        reply_markup=main_menu(),
    )


# =====================================================
# RUN BOT
# =====================================================

def main():
    if TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("ERROR: Set your BotFather token first.")
        return

    if not ADMIN_IDS or 123456789 in ADMIN_IDS:
        print("WARNING: Replace the example ADMIN_IDS value.")

    init_db()

    app = Application.builder().token(TOKEN).build()

    # Broadcast handling runs before regular text handling.
    app.add_handler(
        CommandHandler("broadcast", broadcast_command),
        group=-1,
    )

    app.add_handler(
        CommandHandler("cancelbroadcast", cancel_broadcast),
        group=-1,
    )

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            broadcast_message,
        ),
        group=-1,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("favorites", favorites_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("admin", admin_command))

    app.add_handler(
        CallbackQueryHandler(
            check_join_callback,
            pattern=r"^check_join$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            category_callback,
            pattern=r"^cat:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            favorite_callback,
            pattern=r"^fav:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            favorite_list_callback,
            pattern=r"^favlist:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            show_callback,
            pattern=r"^show:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^admin:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            menu_callback,
            pattern=r"^menu$",
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_name,
        )
    )

    print("Stylish Name Maker Bot started!")

    app.run_polling()


if __name__ == "__main__":
    main()
