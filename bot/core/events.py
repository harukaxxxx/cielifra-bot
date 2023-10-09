import platform
from datetime import datetime

import discord
from discord import DiscordException
from discord.ext.commands import CommandError, CommandNotFound, Context, NotOwner
from rich.box import MINIMAL
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table
import io
import os
from PIL import Image
import json
from datetime import datetime, timezone

from bot import (
    ApplicationContext,
    BaseCog,
    Bot,
    Translator,
    generate_spell,
    get_parameters,
    get_remaining_parameters,
    split_parameter,
)

_ = Translator(__name__)

IMP_TRIGGER_REACTION = os.getenv("IMP_TRIGGER_REACTION")
IMP_REJECT_REACTION = os.getenv("IMP_REJECT_REACTION")


class BaseEventsCog(BaseCog, name="基礎事件"):
    @discord.Cog.listener()
    async def on_ready(self):
        bot = self.bot

        if bot._uptime is not None:
            return

        bot._uptime = datetime.now()

        table_cogs_info = Table(show_edge=False, show_header=False, box=MINIMAL)

        table_cogs_info.add_column(style="blue")
        table_cogs_info.add_column(style="cyan")

        for cog in bot.cogs.values():
            table_cogs_info.add_row(
                cog.__cog_name__,
                f"{docs[:30]}..." if len(docs := cog.__cog_description__) > 20 else docs or "-",
            )

        table_general_info = Table(show_edge=False, show_header=False, box=MINIMAL)

        table_general_info.add_column(style="blue")
        table_general_info.add_column(style="cyan")

        table_general_info.add_row("Prefixes", bot.command_prefix)
        table_general_info.add_row("Default Language", bot.base_lang)
        table_general_info.add_row("python version", platform.python_version())
        table_general_info.add_row("py-cord version", discord.__version__)
        table_general_info.add_row("bot version", bot.__version__)

        table_counts = Table(show_edge=False, show_header=False, box=MINIMAL)

        table_counts.add_column(style="blue")
        table_counts.add_column(style="cyan")

        table_counts.add_row("Servers", str(len(bot.guilds)))
        table_counts.add_row(
            "Unique Users",
            str(len(bot.users)) if bot.intents.members else "-",
        )
        table_counts.add_row("Shards", str(bot.shard_count or "-"))

        self.console.print(
            Columns(
                [
                    Panel(table_cogs_info, title=f"[yellow]cogs - {len(bot.cogs)}"),
                    Panel(table_general_info, title=f"[yellow]{bot.user} login"),
                    Panel(table_counts, title="[yellow]counts"),
                ]
            ),
        )

    @discord.Cog.listener()
    async def on_command(self, ctx: Context):
        self.bot.log.info(
            f"[{ctx.guild.name}] [{ctx.channel.name}] "
            f"{ctx.author} +msg-command+ -> {ctx.command.name}"
        )

    @discord.Cog.listener()
    async def on_application_command(self, ctx: ApplicationContext):
        self.bot.log.info(
            f"[{ctx.guild.name}] [{ctx.channel.name}] "
            f"{ctx.author} +slash-command+ -> {ctx.command.name}"
        )

    @discord.Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, (CommandNotFound, NotOwner)):
            return

        self.log.exception(type(error).__name__, exc_info=error)

    @discord.Cog.listener()
    async def on_application_command_error(
        self,
        ctx: ApplicationContext,
        error: DiscordException,
    ):
        self.log.exception(type(error).__name__, exc_info=error)


class IMPCog(BaseCog, name="咒文讀取"):
    @discord.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        bot = self.bot
        if payload.emoji.name == IMP_TRIGGER_REACTION:
            reaction_member = payload.member
            guild = bot.get_guild(payload.member.guild.id)
            guild_id = guild.id
            channel = bot.get_channel(payload.channel_id)
            channel_id = payload.channel_id
            message = await channel.fetch_message(int(payload.message_id))
            attachments = message.attachments
            if attachments:
                vaild_attachment = False
                for attachment in attachments:
                    # get magic id
                    magic_id = f"{guild_id}-{channel_id}-{attachment.id}"

                    # find exists magic data
                    try:
                        with open("logs/magics.json", "r") as file:
                            magic_dict = json.load(file)
                    except FileNotFoundError:
                        magic_dict = {}
                    except json.decoder.JSONDecodeError:
                        magic_dict = {}
                    if magic_id in magic_dict:
                        self.log.info(f"Cielifra 在魔法手帳目錄找到魔法 {magic_id}，正在努力翻找手帳…")
                        vaild_attachment = True
                    else:
                        # check attachment is png which have parameters
                        if attachment.filename.endswith(".png"):
                            image_data = io.BytesIO(await attachment.read())
                            with Image.open(image_data) as img:
                                img.load()
                                try:
                                    parameter_info = img.info["parameters"]
                                    vaild_attachment = True
                                    self.log.info(
                                        f"Cielifra 在魔法手帳目錄找不到魔法 {magic_id}，正在努力施展無限魔法投影解析魔法中…"
                                    )
                                except KeyError:
                                    continue

                        # buildup magic data
                        title = f"『{generate_spell(magic_id)}』"
                        nprompt_index = parameter_info.find("Negative prompt: ")
                        steps_index = parameter_info.find("Steps: ")
                        prompts = parameter_info[0:nprompt_index]
                        nprompts = parameter_info[nprompt_index + 17 : steps_index]
                        extras = parameter_info[steps_index - 1 : len(parameter_info)]
                        parameters = {
                            "Steps": None,
                            "CFG scale": None,
                            "Seed": None,
                            "Sampler": None,
                            "Model": None,
                            "Model hash": None,
                            "VAE": None,
                            "VAE hash": None,
                            "Clip skip": None,
                            "Size": None,
                            "Version": None,
                            "Hires upscale": None,
                            "Hires steps": None,
                            "Hires upscaler": None,
                            "Denoising strength": None,
                            "Lora hashes": None,
                        }
                        for parameter in parameters.keys():
                            parameters[parameter] = get_parameters(extras, f"{parameter}: ")
                        extra_parameters = get_remaining_parameters(parameters, extras)
                        timestamp = datetime.now(timezone.utc).isoformat()
                        try:
                            author = await message.guild.fetch_member(message.author.id)
                            author_name = author.nick if author.nick is not None else author.name
                            author_avatar_url = (
                                author.avatar.url
                                if author.avatar is not None
                                else f"https://fakeimg.pl/300x300/?text={author_name[0]}"
                            )
                        except discord.errors.NotFound:
                            author_name = "未知的咒文師"
                            author_avatar_url = f"https://fakeimg.pl/300x300/?text={author_name[0]}"
                        guild_name = guild.name
                        guild_icon_url = (
                            guild.icon.url
                            if guild.icon is not None
                            else f"https://fakeimg.pl/300x300/?text={guild_name[0]}"
                        )
                        channel_name = channel.name
                        footer_text = f"來自「{guild_name}」{channel_name}頻道"
                        message_link = message.jump_url

                        # Save magic_data into magic.json
                        magic_data = {
                            magic_id: {
                                "title": title,
                                "prompt": prompts,
                                "nprompt": nprompts,
                                "parameters": parameters,
                                "extra_info": extra_parameters,
                                "timestamp": timestamp,
                                "image_url": attachment.url,
                                "author": {"name": author_name, "icon_url": author_avatar_url},
                                "footer": {"text": footer_text, "icon_url": guild_icon_url},
                                "message_url": message_link,
                            }
                        }
                        # save magic data to magic.json
                        try:
                            with open("logs/magics.json", "r", encoding="utf-8") as file:
                                existing_magic_data = json.load(file)
                        except FileNotFoundError:
                            existing_magic_data = {}
                        except json.decoder.JSONDecodeError:
                            existing_magic_data = {}

                        for id, data in magic_data.items():
                            existing_magic_data[id] = data

                        with open("logs/magics.json", "w", encoding="utf-8") as file:
                            json.dump(existing_magic_data, file, ensure_ascii=False, indent=2)

                    # read magic data from magic.json
                    with open("logs/magics.json", "r") as file:
                        magic_dict = json.load(file)
                    magic_data = {magic_id: magic_dict[magic_id]}

                    # buildup embed fields
                    embed_fields = []

                    # separate prompt under 1024
                    prompt_list = split_parameter(magic_data[magic_id]["prompt"])
                    prompt_fields = []
                    for i, parameter in enumerate(prompt_list, 1):
                        name = f"Prompt {i}" if len(prompt_list) > 1 else "Prompt"
                        prompt_fields.append(
                            {
                                "name": name,
                                "value": parameter,
                            }
                        )
                    embed_fields.extend(prompt_fields)

                    # separate nprompt under 1024
                    nprompt_list = split_parameter(magic_data[magic_id]["nprompt"])
                    nprompt_fields = []
                    for i, parameter in enumerate(nprompt_list, 1):
                        name = (
                            f"Negative Prompt {i}" if len(nprompt_list) > 1 else "Negative Prompt"
                        )
                        nprompt_fields.append(
                            {
                                "name": name,
                                "value": parameter,
                            }
                        )
                    embed_fields.extend(nprompt_fields)

                    # add parameter fields
                    parameter_field = [
                        {"name": "Parameters", "value": ""},
                        {
                            "name": "Steps",
                            "value": magic_data[magic_id]["parameters"]["Steps"],
                            "inline": True,
                        },
                        {
                            "name": "CFG scale",
                            "value": magic_data[magic_id]["parameters"]["CFG scale"],
                            "inline": True,
                        },
                        {
                            "name": "Seed",
                            "value": magic_data[magic_id]["parameters"]["Seed"],
                            "inline": True,
                        },
                        {
                            "name": "Sampler",
                            "value": magic_data[magic_id]["parameters"]["Sampler"],
                            "inline": True,
                        },
                        {
                            "name": "Model",
                            "value": magic_data[magic_id]["parameters"]["Model"],
                            "inline": True,
                        },
                        {
                            "name": "Model hash",
                            "value": magic_data[magic_id]["parameters"]["Model hash"],
                            "inline": True,
                        },
                        {
                            "name": "VAE",
                            "value": magic_data[magic_id]["parameters"]["VAE"],
                            "inline": True,
                        },
                        {
                            "name": "VAE hash",
                            "value": magic_data[magic_id]["parameters"]["VAE hash"],
                            "inline": True,
                        },
                        {
                            "name": "Size",
                            "value": magic_data[magic_id]["parameters"]["Size"],
                            "inline": True,
                        },
                        {
                            "name": "Version",
                            "value": magic_data[magic_id]["parameters"]["Version"],
                            "inline": True,
                        },
                    ]
                    embed_fields.extend(parameter_field)

                    # add hires fields if exists
                    if magic_data[magic_id]["parameters"]["Hires upscale"] != "-":
                        hires_fields = [
                            {"name": "Hires info", "value": ""},
                            {
                                "name": "Hires upscale",
                                "value": magic_data[magic_id]["parameters"]["Hires upscale"],
                                "inline": True,
                            },
                            {
                                "name": "Hires steps",
                                "value": magic_data[magic_id]["parameters"]["Hires steps"],
                                "inline": True,
                            },
                            {
                                "name": "Hires upscaler",
                                "value": magic_data[magic_id]["parameters"]["Hires upscaler"],
                                "inline": True,
                            },
                            {
                                "name": "Denoising strength",
                                "value": magic_data[magic_id]["parameters"]["Denoising strength"],
                                "inline": True,
                            },
                        ]
                        embed_fields.extend(hires_fields)
                    # add lora hashes field
                    if magic_data[magic_id]["parameters"]["Lora hashes"] != "-":
                        lora_hashes_fields = [
                            {
                                "name": "Lora hashes",
                                "value": magic_data[magic_id]["parameters"]["Lora hashes"],
                            },
                        ]
                        embed_fields.extend(lora_hashes_fields)

                    # separate extra info under 1024
                    extra_info_list = split_parameter(magic_data[magic_id]["extra_info"])
                    extra_info_fields = []
                    for i, parameter in enumerate(extra_info_list, 1):
                        name = f"Extra info {i}" if len(extra_info_list) > 1 else "Extra info"
                        extra_info_fields.append(
                            {
                                "name": name,
                                "value": parameter,
                            }
                        )
                    embed_fields.extend(extra_info_fields)

                    # build up embed dict
                    embed_dict = {
                        "title": magic_data[magic_id]["title"],
                        "type": "rich",
                        "description": "",
                        "color": discord.Colour.from_rgb(127, 0, 32).value,
                        "fields": embed_fields,
                        "timestamp": magic_data[magic_id]["timestamp"],
                        "image": {"url": magic_data[magic_id]["image_url"]},
                        "thumbnail": {
                            "url": "https://cdn.discordapp.com/avatars/1114773909888307280/bd205368c333e1a63444b358bbdc4340.png"
                        },
                        "author": {
                            "name": magic_data[magic_id]["author"]["name"],
                            "icon_url": magic_data[magic_id]["author"]["icon_url"],
                        },
                        "footer": {
                            "text": magic_data[magic_id]["footer"]["text"],
                            "icon_url": magic_data[magic_id]["footer"]["icon_url"],
                        },
                        "url": magic_data[magic_id]["message_url"],
                    }

                    # create embed
                    magic_embed = discord.Embed.from_dict(embed_dict)

                    # Send DM
                    # embed = discord.Embed(
                    #     title=magic_data["title"], description=magic_data["description"], colour=discord.Colour.from_rgb(magic_data["colour"](0), 0, 32), url=message_link
                    # )
                    # dm_channel = await reaction_member.create_dm()

                    dm_channel = await reaction_member.create_dm()
                    try:
                        await dm_channel.send(embed=magic_embed)
                    except discord.errors.HTTPException as exception_occurred:
                        if exception_occurred.status == 400 and exception_occurred.code == 50035:
                            await dm_channel.send(
                                content=_(
                                    "無限魔法投影已超出負荷，Cielifra 的法力正在耗盡！\n請手動下載 PNG 使用 sd-webui 的 PNG info 功能獲取咒文。\n原始訊息的連結是：{message_url}"
                                ).format(message_url=message_link)
                            )
                            await message.remove_reaction(IMP_TRIGGER_REACTION, reaction_member)
                            await message.add_reaction(IMP_REJECT_REACTION)
                        else:
                            self.log.exception("An HTTPException occurred:", exception_occurred)
                    self.log.info(f"Cielifra 成功將魔法 {magic_id} 的咒文私訊給 {reaction_member.name}了。")
                if vaild_attachment is False:
                    await message.remove_reaction(IMP_TRIGGER_REACTION, reaction_member)
                    await message.add_reaction(IMP_REJECT_REACTION)
            else:
                await message.remove_reaction(IMP_TRIGGER_REACTION, reaction_member)


def setup(bot: "Bot"):
    bot.add_cog(BaseEventsCog(bot))
    bot.add_cog(IMPCog(bot))
