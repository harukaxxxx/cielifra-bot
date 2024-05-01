import io
import aiohttp
import discord
from bot import BaseCog, Bot, Translator, cog_i18n

_ = Translator(__name__)


async def send_bookmark_dm(reaction_member, dm_message, embed_dict, attachments):
    dm_embed = discord.Embed.from_dict(embed_dict)
    dm_channel = await reaction_member.create_dm()
    try:
        if attachments:
            for attachment in attachments:
                attachment_url = str(attachment)
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment_url) as resp:
                        if resp.status != 200:
                            return
                        data = io.BytesIO(await resp.read())
                        file = discord.File(
                            data, attachment_url.split('?', maxsplit=1)[0].split('/')[-1]
                        )
                        await dm_channel.send(file=file)
        await dm_channel.send(content=dm_message, embed=dm_embed)
    except discord.DiscordException as error:
        error_message = f"無法給用戶 {reaction_member} 發送書籤私人訊息。錯誤信息：{error}"
        print(error_message)


@cog_i18n
class BookmarkCog(BaseCog, name="書籤"):
    @discord.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        bot = self.bot
        if payload.emoji.name == "🔖":
            channel = await bot.get_or_fetch_channel(payload.channel_id)
            message = await channel.fetch_message(int(payload.message_id))
            guild = message.guild
            guild_avatar_url = guild.icon.url if guild.icon else ""
            author = await message.guild.fetch_member(message.author.id)
            author_name = author.nick if author.nick is not None else author.name
            author_avatar_url = author.avatar.url if author.avatar else ""

            if channel is None:
                print("Channel not found.")
                return

            embed_dict = {
                "type": "rich",
                "description": f"{message.content}\n\n查看原始訊息：{message.jump_url}",
                "color": discord.Colour.from_rgb(127, 0, 32).value,
                "author": {
                    "name": author_name,
                    "url": f"http://discordapp.com/users/{message.author.id}",
                    "icon_url": author_avatar_url,
                },
                "footer": {
                    "text": f"來自「{guild.name}」{channel.name}頻道",
                    "icon_url": guild_avatar_url,
                },
            }
            reaction_member = payload.member
            await send_bookmark_dm(reaction_member, "", embed_dict, message.attachments)


def setup(bot: "Bot"):
    bot.add_cog(BookmarkCog(bot))
