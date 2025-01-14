import re
from requests import get
import wget
from uuid import uuid4
from pyrogram import Client, filters
from pyrogram.errors import MediaEmpty, MessageIdInvalid, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto, InlineQuery, InlineQueryResultPhoto
from userge import Message, config as Config, userge
from iytdl import main
from ...builtin import sudo


if userge.has_bot:
    def check_owner(func):
        async def wrapper(_, c_q: CallbackQuery):
            if c_q.from_user and c_q.from_user.id in (list(Config.OWNER_ID) + list(sudo.USERS)):
                try:
                    await func(c_q)
                except MessageNotModified:
                    await c_q.answer("Nothing Found to Refresh 🤷‍♂️", show_alert=True)
                except MessageIdInvalid:
                    await c_q.answer(
                        "Sorry, I Don't Have Permissions to edit this 😔",
                        show_alert=True
                    )
            else:
                user_dict = await userge.bot.get_user_dict(Config.OWNER_ID[0])
                await c_q.answer(
                    f"Only {user_dict['flname']} Can Access this...! Build Your Own @TheUserge 🤘",
                    show_alert=True)
        return wrapper


    ytdl = main.iYTDL(Config.LOG_CHANNEL_ID, download_path="userge/plugins/custom/iytdl/", silent=True)

    # https://gist.github.com/silentsokolov/f5981f314bc006c82a41
    regex = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})')
    YT_DB = {}

    def rand_key():
        return str(uuid4())[:8]


    @userge.on_cmd("iytdl", about={
        'header': "Advanced YTDL",
        'usage': "{tr}iytdl URL or Query"})
    async def iytdl_ub_cmd(m: Message):
        query = m.input_str
        if not query:
            return await m.reply("Nothing to search for")
        if m.client.is_bot:
            match = regex.match(query)
            if match is None:
                search_key = rand_key()
                YT_DB[search_key] = query
                search = await main.VideosSearch(query).next()
                if search["result"] == []:
                    return 
                i = search['result'][0]
                out = f"<b><a href={i['link']}>{i['title']}</a></b>"
                out+=f"\nPublished {i['publishedTime']}\n"
                out+=f"\n<b>❯ Duration:</b> {i['duration']}"
                out+=f"\n<b>❯ Views:</b> {i['viewCount']['short']}"
                out+=f"\n<b>❯ Uploader:</b> <a href={i['channel']['link']}>{i['channel']['name']}</a>\n\n"
                if i['descriptionSnippet']:
                    for t in i['descriptionSnippet']:
                        out+=t['text']
                btn = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(f"1/{len(search['result'])}", callback_data=f"ytdl_scroll|{search_key}|1")
                        ],
                        [
                            InlineKeyboardButton("Download", callback_data=f"yt_gen|{i['id']}")
                        ]
                    ]
                )
                img = i["thumbnails"][1 if len(i["thumbnails"])>1 else 0]["url"].split("?")[0]
                caption = out
                markup = btn
            else:
                key = match.group("id")
                x = await main.Extractor().get_download_button(key)
                rand = rand_key()
                novar = wget.download(x.image_url, out=f"{rand}.png") # var to ensure that it completes download
                img = f"{rand}.png"
                caption=x.caption
                markup=x.buttons
            try:
                await userge.bot.send_photo(m.chat.id, img, caption=caption, reply_markup=markup)
            except MediaEmpty:
                img = "https://camo.githubusercontent.com/8486ea960b794cefdbbba0a8ef698d04874152c8e24b3b26adf7f50847d4a3a8/68747470733a2f2f692e696d6775722e636f6d2f51393443444b432e706e67"
                await userge.bot.send_photo(m.chat.id, img, caption=caption, reply_markup=markup)
        else:
            username = (await userge.bot.get_me()).username
            x = await userge.get_inline_bot_results(username, f"ytdl {query}")
            await userge.send_inline_bot_result(chat_id=m.chat.id, query_id=x.query_id, result_id=x.results[0].id)



    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"ytdl_scroll\|(.*)"))
    @check_owner
    async def ytdl_scroll_callback(cq: CallbackQuery):
        callback = cq.data.split("|")
        search_key = callback[1]
        page = int(callback[2])
        query = YT_DB[search_key]
        search = await main.VideosSearch(query).next()
        i = search['result'][page]
        out = f"<b><a href={i['link']}>{i['title']}</a></b>"
        out+=f"\nPublished {i['publishedTime']}\n"
        out+=f"\n<b>❯ Duration:</b> {i['duration']}"
        out+=f"\n<b>❯ Views:</b> {i['viewCount']['short']}"
        out+=f"\n<b>❯ Uploader:</b> <a href={i['channel']['link']}>{i['channel']['name']}</a>\n\n"
        if i['descriptionSnippet']:
            for t in i['descriptionSnippet']:
                out+=t['text']
        scroll_btn = [
            [
                InlineKeyboardButton(f"Back", callback_data=f"ytdl_scroll|{search_key}|{page-1}"),
                InlineKeyboardButton(f"{page+1}/{len(search['result'])}", callback_data=f"ytdl_scroll|{search_key}|{page+1}")
            ]
        ]
        if page==0:
            if len(search['result'])==1:
                return await cq.answer("That's the end of list", show_alert=True)
            scroll_btn = [[scroll_btn.pop().pop()]]
        elif page==(len(search['result'])-1):
            scroll_btn = [[scroll_btn.pop().pop(0)]]
        btn = [
            [
                InlineKeyboardButton("Download", callback_data=f"yt_gen|{i['id']}")
            ]
        ]
        btn = InlineKeyboardMarkup(scroll_btn+btn)
        try:
            await cq.edit_message_media(InputMediaPhoto(i["thumbnails"][1 if len(i["thumbnails"])>1 else 0]["url"].split("?")[0], caption=out), reply_markup=btn)
        except MediaEmpty:
            await cq.edit_message_media(InputMediaPhoto("https://camo.githubusercontent.com/8486ea960b794cefdbbba0a8ef698d04874152c8e24b3b26adf7f50847d4a3a8/68747470733a2f2f692e696d6775722e636f6d2f51393443444b432e706e67", caption=out), reply_markup=btn)


    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"yt_(gen|dl)\|(.*)"))
    @check_owner
    async def ytdl_gendl_callback(cq: CallbackQuery):
        callback = cq.data.split("|")
        key = callback[1]
        if callback[0]=="yt_gen":
            x = await main.Extractor().get_download_button(key)
            await cq.edit_message_caption(caption=x.caption, reply_markup=x.buttons)
        else:
            uid = callback[2]
            type_ = callback[3]
            if type_ == "a":
                format_ = "audio"
            else:
                format_ = "video"
            upload_key = await ytdl.download("https://www.youtube.com/watch?v="+key, uid, format_, cq, True, 3)
            await ytdl.upload(userge.bot, upload_key, format_, cq, True)
    
    
    @userge.bot.on_inline_query(
        filters.create(
            lambda _, __, inline_query: (
                inline_query.query
                and inline_query.query.startswith("ytdl ")
                and inline_query.from_user.id in (list(Config.OWNER_ID) + list(sudo.USERS))
            ),
            name="iYTDL"
        ),
        group=-2
    )
    async def iytdl_inline(client: Client, iq: InlineQuery):
        query = iq.query.split("ytdl ", 1)[1]
        match = regex.match(query)
        if match is None:
            search_key = rand_key()
            YT_DB[search_key] = query
            i: list = (await main.VideosSearch(query=query).next())['result'][0]
            results = []
            key = i['id']
            img = f"https://i.ytimg.com/vi/{key}/maxresdefault.jpg"
            thumb = f"https://i.ytimg.com/vi/{key}/default.jpg"
            out = f"<b><a href={i['link']}>{i['title']}</a></b>"
            out+=f"\nPublished {i['publishedTime']}\n"
            out+=f"\n<b>❯ Duration:</b> {i['duration']}"
            out+=f"\n<b>❯ Views:</b> {i['viewCount']['short']}"
            out+=f"\n<b>❯ Uploader:</b> <a href={i['channel']['link']}>{i['channel']['name']}</a>\n\n"
            if i['descriptionSnippet']:
                for t in i['descriptionSnippet']:
                    out+=t['text']
            scroll_btn = [
                [
                    InlineKeyboardButton(f"1/{len(i)}", callback_data=f"ytdl_scroll|{search_key}|1")
                ]
            ]
            if len(i)==1:
                scroll_btn = []
            btn = [
                [
                    InlineKeyboardButton("Download", callback_data=f"yt_gen|{key}")
                ]
            ]
            btn = InlineKeyboardMarkup(scroll_btn+btn)
            results.append(
                InlineQueryResultPhoto(
                    photo_url=img,
                    thumb_url=thumb,
                    caption=out,
                    reply_markup=btn,
                )
            )
        else:
            key = match.group("id")
            x = await main.Extractor().get_download_button(key)
            img = f"https://i.ytimg.com/vi/{key}/maxresdefault.jpg"
            thumb = f"https://i.ytimg.com/vi/{key}/default.jpg"
            if get(img).status_code != 200:
                thumb = img = "https://camo.githubusercontent.com/8486ea960b794cefdbbba0a8ef698d04874152c8e24b3b26adf7f50847d4a3a8/68747470733a2f2f692e696d6775722e636f6d2f51393443444b432e706e67"
            results = [
                InlineQueryResultPhoto(
                    photo_url=img,
                    thumb_url=thumb,
                    caption=x.caption,
                    reply_markup=x.buttons,
                )
            ]
        await iq.answer(results=results, is_gallery=False, is_personal=True)
        iq.stop_propagation()
