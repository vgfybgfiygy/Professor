class script(object):
    START_TXT = """<b>👋 හෙලෝ {},

මට පුළුවන් ඕනෑම Movie එකක් හරි TV Series එකක් හරි Auto Filter ක්‍රමයට ලබා දෙන්න... 🥳

ඔයාට කරන්න තියෙන්නේ මාව Group එකකට Add කරලා මට Admin දෙන්න විතරයි... 😌

ඉතුරු හරිය මං බලා ගන්නම්.... 😎</b>"""

    FORCESUB_TXT = """<b>👋 හෙලෝ {},

මුලින්ම මගේ Updates Channel එකට Join වෙන්න, ඊට පස්සේ ආයේ උත්සාහ කරන්න... 😇</b>"""

    ABOUT_TXT = """★ My Name: <a href=https://t.me/{}>{}</a>
★ Creator: <a href=https://t.me/Hansaka_Anuhas>Hansaka Anuhas</a> 🇱🇰
★ Bot Server: <a href=https://www.linode.com>VPS</a>
★ Database: <a href=https://www.mongodb.com>MongoDB</a>"""

    MANUALFILTERS_TXT = """• /filter or /add - Add Filter
• /filters or /viewfilters - List All Filters
• /del - Delete Filter
• /delall - Delete All Filters"""

    BUTTONS_TXT = """<b>URL Buttons:</b>
<code>[Button Text](buttonurl:https://t.me/{})</code>

<b>Alert Buttons:</b>
<code>[Button Text](buttonalert:Alert Message)</code>"""

    AUTOFILTERS_TXT = """<b>ඔයාගේ Movies සහ TV Series මට දෙන්නේ මෙහෙමයි:

1. ඔයාට Movies හරි TV Series හරි Channel එකක් තියෙනවනම්, මාව ඒකට Add කරලා මට Admin දෙන්න.
2. ඔයාගේ Channel එකේ ඔයාට කැමති Message එකක් මට Forward කරන්න.
3. ඉතුරු හරිය මං බලා ගන්නම්.</b>"""

    CONNECTIONS_TXT = """• /connect - Connect PM
• /disconnect - Disconnect PM
• /connections - List All Connections"""

    EXTRAMODS_TXT = """• /id - User ID
• /info - User Informations
• /imdb or /search - IMDb Search
• /status - Bot Database Status
• /settings - Change Group Settings
• /set_template - Set IMDb Template
• /link - Create Link One Post
• /batch - Create Link Multiple Posts"""

    OWNERMODS_TXT = """• /users - List All Users
• /chats - List All Groups
• /ban - Ban User
• /unban - Unban User
• /leave - Leave Group
• /disable - Disable Group
• /enable - Re-enable Group
• /invite_link - Generate Group Link
• /users_broadcast - Broadcast Message All Users
• /groups_broadcast - Broadcast Message All Groups"""

    STATUS_TXT = """★ Total Files: <code>{}</code>
★ Total Users: <code>{}</code>
★ Total Groups: <code>{}</code>
★ Used Storage: <code>{}</code>
★ Free Storage: <code>{}</code>"""

    LOG_TEXT_G = """#NewGroup
Title: {}
ID: <code>{}</code>
Total Members: {}
Added by: {}"""

    LOG_TEXT_P = """#NewUser
Name: {}
ID: <code>{}</code>"""
    
    NO_RESULT = """#NoResult
Group: {}
Name: {}
ID: <code>{}</code>
Message: {}"""
