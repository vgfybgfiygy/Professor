import random
import asyncio
import re
import ast
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, LOG_CHANNEL, SUPPORT_CHAT, PICS, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, AUTOFILTER, AUTO_DELETE, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        settings = await get_settings(message.chat.id)
        await auto_filter(client, message) if settings['autofilter'] else None


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(f"හෙලෝ {query.from_user.first_name},\nඅනුන්ගේ ඒවා ඔබන්න එපා!", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"⭐️ {get_size(file.file_size)} 👉 {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"⭐️ {get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"👉 {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:

        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 Pages {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
        btn.append(
            [
                InlineKeyboardButton("✅ How To Download ✅", callback_data="howtodownload")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])
        btn.append(
            [
                InlineKeyboardButton("✅ How To Download ✅", callback_data="howtodownload")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
            ]
        )
        btn.append(
            [
                InlineKeyboardButton("✅ How To Download ✅", callback_data="howtodownload")]
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(f"හෙලෝ {query.from_user.first_name},\nඅනුන්ගේ ඒවා ඔබන්න එපා!", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('බලමු මගේ Database එකේ තියෙනවද කියලා...')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            await bot.send_message(LOG_CHANNEL, script.NO_RESULT.format(query.message.chat.title, query.from_user.mention, query.from_user.id, movie))
            k = await query.message.edit(f"<b>👋 හෙලෝ {query.from_user.mention},\n\nඔහොම Movie එකක් වත් TV Series එකක් වත් මගේ Database එකේ හොයා ගන්න නෑ, නැත්නම් තාම Release වෙලා නැතුව ඇති... 😔</b>")
            await asyncio.sleep(60)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!", quote=True)
                    return await query.answer('Loading...')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Loading...')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Loading...')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name: **{title}**\nGroup ID: `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Loading...')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('Loading...')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Loading...')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Loading...')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections! Connect to some groups first.",
            )
            return await query.answer('Loading...')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details:\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        user = query.message.reply_to_message.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(f"හෙලෝ {query.from_user.first_name},\nඅනුන්ගේ ඒවා ඔබන්න එපා!", show_alert=True)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
    
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❤️‍🔥 Please Share and Support ❤️‍🔥', url=f'https://t.me/share/url?url=https://t.me/{temp.U_NAME}')]])
                )
                await client.send_message(chat_id=query.from_user.id, text=f"<b>👋 හෙලෝ {query.from_user.mention},\n\nඔයා Download කරන්නේ x265 File එකක් නම් අනිවාරයෙන්ම ඔයාගේ Device එක x265 Codec එකට Support කරනවද කියලා දැනගෙන Download කරන්න, විශේෂයෙන්ම මේක කියන්නේ Phone එකෙන් බලනවනම්... 😊</b>\n\n<i>Happy Downloading and Come Again... ❤️</i>")
                await query.answer(f'හෙලෝ {query.from_user.first_name},\nඔයාගේ Inbox එක බලන්න!', show_alert=True)
        except UserIsBlocked:
            await query.answer(f'හෙලෝ {query.from_user.first_name},\nඔයා මාව Block කරලනේ, මාව Unblock කරලා ආයේ උත්සාහ කරන්න...', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer(f"හෙලෝ {query.from_user.first_name},\nමම ඔයාගේ උත්සාහ කිරීමට කැමතියි, ඒත් තරහ නැතුව මගේ Update Channel එකට Join වෙලා ආයේ උත්සාහ කරන්න...", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❤️‍🔥 Please Share and Support ❤️‍🔥', url=f'https://t.me/share/url?url=https://t.me/{temp.U_NAME}')]])
        )
        await client.send_message(chat_id=query.from_user.id, text=f"<b>👋 හෙලෝ {query.from_user.mention},\n\nඔයා Download කරන්නේ x265 File එකක් නම් අනිවාරයෙන්ම ඔයාගේ Device එක x265 Codec එකට Support කරනවද කියලා දැනගෙන Download කරන්න, විශේෂයෙන්ම මේක කියන්නේ Phone එකෙන් බලනවනම්... 😊</b>\n\n<i>Happy Downloading and Come Again... ❤️</i>")
    elif query.data == "pages":
        await query.answer()
    elif query.data == "howtodownload":
        await query.answer(f"හෙලෝ {query.from_user.first_name},\nමුලින්ම ඔය උඩින් තියන Buttons වළින් ඔයාට ඕන Movie එකේ හරි TV Series එකේ හරි නම හරියට බලලා ඔබන්න, ඊට පස්සේ Open වෙන බොටාගේ Start Button එක ඔබන්න...", show_alert=True)
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('➕ Add Me To Your Group ➕', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton('❓ Help', callback_data='help'),
            InlineKeyboardButton('ℹ️ About', callback_data='about')
        ], [
            InlineKeyboardButton('❌ Close ❌', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer('Loading...')
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('Filters', callback_data='filters'),
            InlineKeyboardButton('Connections', callback_data='connections')
       ], [
            InlineKeyboardButton('Extra Mods', callback_data='extramods')
       ], [
            InlineKeyboardButton('◀️ Back', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text='Help',
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('Report Bugs and Feedback', url=f'https://t.me/{SUPPORT_CHAT}')
       ], [
            InlineKeyboardButton('Status', callback_data='status'),
            InlineKeyboardButton('Source Code', url='https://github.com/SL-Auto-Filter-Bot/Professor')
       ], [
            InlineKeyboardButton('◀️ Back', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "filters":
        buttons = [[
            InlineKeyboardButton('Manual Filters', callback_data='manualfilters'),
            InlineKeyboardButton('Auto Filters', callback_data='autofilters')
        ], [
            InlineKeyboardButton('◀️ Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text='Filters',
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manualfilters":
        buttons = [[
            InlineKeyboardButton('Buttons', callback_data='buttons')
        ], [
            InlineKeyboardButton('◀️ Back', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUALFILTERS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "buttons":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='manualfilters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTONS_TXT.format(temp.U_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilters":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTERS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "connections":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTIONS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extramods":
        buttons = [[
            InlineKeyboardButton('Owner Mods', callback_data='ownermods')
        ], [
            InlineKeyboardButton('◀️ Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMODS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "ownermods":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='extramods')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.OWNERMODS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "status":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("First /connect and then Change /settings")
            return await query.answer('Loading...')

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Bot Inbox', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["botpm"] else '❌ No',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('IMDb Poster', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spelling Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome Message', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Auto Filter', callback_data=f'setgs#autofilter#{settings["autofilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["autofilter"] else '❌ No',
                                         callback_data=f'setgs#autofilter#{settings["autofilter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Auto Delete', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('One Hours' if settings["auto_delete"] else '❌ No',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('Loading...')


async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"⭐️ {get_size(file.file_size)} 👉 {file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"⭐️ {get_size(file.file_size)}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"👉 {file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")]
        )
        btn.append(
            [
                InlineKeyboardButton("✅ How To Download ✅", callback_data="howtodownload")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
        btn.append(
            [
                InlineKeyboardButton("✅ How To Download ✅", callback_data="howtodownload")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"✅ I Found Your Query: <code>{search}</code>\n\n🗣 Requested by: {message.from_user.mention}\n©️ Powered by: <b>{message.chat.title}</b>"
    if imdb and imdb.get('poster'):
        try:
            k = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                          reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(3600)
            await k.delete() if settings['auto_delete'] else None
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            k = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(3600)
            await k.delete() if settings['auto_delete'] else None
        except Exception as e:
            logger.exception(e)
            k = await message.reply_photo(photo="https://telegra.ph/file/f1da7639c429a6a0dba80.jpg", caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(3600)
            await k.delete() if settings['auto_delete'] else None
    else:
        k = await message.reply_photo(photo="https://telegra.ph/file/f1da7639c429a6a0dba80.jpg", caption=cap, reply_markup=InlineKeyboardMarkup(btn))
        await asyncio.sleep(3600)
        await k.delete() if settings['auto_delete'] else None
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply_photo(photo=random.choice(PICS), caption=f"<b>👋 හෙලෝ {msg.from_user.mention},\n\nඔයා ඉල්ලපු Movie එක හරි TV Series එක හරි මට හොයා ගන්න බෑ... 😢</b>")
        await asyncio.sleep(60)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        k = await msg.reply_photo(photo=random.choice(PICS), caption=f"<b>👋 හෙලෝ {msg.from_user.mention},\n\nඔයා ඉල්ලපු Movie එක හරි TV Series එක හරි මට හොයා ගන්න බෑ, බලන්න ඔයාගේ Spellings හරිද කියලා... 😉</b>")
        await asyncio.sleep(60)
        await k.delete()
        return
    SPELL_CHECK[msg.id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="❌ Close ❌", callback_data=f'spolling#{user}#close_spellcheck')])
    k = await msg.reply_photo(photo=random.choice(PICS), caption=f"<b>👋 හෙලෝ {msg.from_user.mention},\n\nඔයා ඉල්ලපු Movie එක හරි TV Series එක හරි මට හොයා ගන්න බැරි වුනා, බලන්න මෙතන තියෙනවද කියලා... 👇</b>",
                    reply_markup=InlineKeyboardMarkup(btn))
    await asyncio.sleep(60)
    await k.delete()


async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
