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
from PIL import Image

from bot import (
    ApplicationContext,
    BaseCog,
    Bot,
    Translator,
    generate_spell,
    extra_parameter,
    split_prompt,
)

_ = Translator(__name__)


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
        TRIGGER_REACTION = "🤩"
        bot = self.bot
        if payload.emoji.name == TRIGGER_REACTION:
            reaction_member = payload.member
            channel = bot.get_channel(payload.channel_id)
            channel_id = payload.channel_id
            channel_name = channel.name
            message = await channel.fetch_message(int(payload.message_id))
            message_link = message.jump_url
            guild = bot.get_guild(payload.member.guild.id)
            guild_name = guild.name
            guild_icon_url = (
                guild.icon.url
                if guild.icon != None
                else f"https://fakeimg.pl/300x300/?text={guild_name[0]}"
            )
            author = await message.guild.fetch_member(message.author.id)
            author_name = author.nick if author.nick != None else author.name
            author_avatar_url = (
                author.avatar.url
                if author.avatar != None
                else f"https://fakeimg.pl/300x300/?text={author_name[0]}"
            )

            attachments = message.attachments

            if attachments:
                for attachment in attachments:
                    attachment_id = f"{channel_id}-{attachment.id}"
                    # Check if the attachment is a PNG file
                    if attachment.filename.endswith(".png"):
                        # Read attachment data into memory
                        image_data = io.BytesIO(await attachment.read())

                        # Open the image from memory
                        with Image.open(image_data) as img:
                            img.load()
                            try:
                                parameter = img.info["parameters"]
                            except KeyError:
                                # Parameters not found
                                await message.remove_reaction(TRIGGER_REACTION, reaction_member)
                                await message.add_reaction("❎")
                                continue

                    else:
                        # Not a PNG file
                        await message.remove_reaction(TRIGGER_REACTION, reaction_member)
                        await message.add_reaction("❎")
                        return

                    # Process parameter
                    nprompt_index = parameter.find("Negative prompt: ")
                    steps_index = parameter.find("Steps: ")
                    prompts = parameter[0:nprompt_index]
                    nprompts = parameter[nprompt_index + 17 : steps_index]
                    extras = parameter[steps_index : len(parameter)]

                    # Building DM embed message
                    dm_channel = await reaction_member.create_dm()
                    title = f"『{generate_spell(attachment_id)}』"
                    color = discord.Colour.from_rgb(127, 0, 32)
                    embed = discord.Embed(
                        title=title, description="", colour=color, url=message_link
                    )

                    # Setup prompt field
                    prompt_list = split_prompt(prompts)
                    if len(prompt_list) > 1:
                        for i, prompt in enumerate(prompt_list, 1):
                            embed.add_field(name=f"Prompt {i}", value=prompt, inline=False)
                    else:
                        embed.add_field(name="Prompt", value=prompts, inline=False)

                    # Setup negtive prompt field
                    nprompt_list = split_prompt(nprompts)
                    if len(nprompt_list) > 1:
                        for i, nprompt in enumerate(nprompt_list, 1):
                            embed.add_field(
                                name=f"Negative Prompt {i}", value=nprompt, inline=False
                            )
                    else:
                        embed.add_field(name="Negative Prompt", value=nprompts, inline=False)

                    # Setup parameter field
                    parameter_fields = [
                        "Steps",
                        "CFG scale",
                        "Seed",
                        "Sampler",
                        "Model",
                        "Model hash",
                        "Size",
                        "Version",
                        "Hires upscale",
                        "Hires steps",
                        "Hires upscaler",
                        "Denoising strength",
                    ]
                    embed.add_field(name="Parameters", value="", inline=False)
                    for field in parameter_fields:
                        # check if Hires exist print hires info else break loop
                        if field == "Hires upscale" and parameter.find("Hires upscale: ") < 0:
                            break
                        elif field == "Hires upscale":
                            embed.add_field(name="Hires info", value="", inline=False)
                        embed.add_field(
                            name=field,
                            value=extra_parameter(parameter, f"{field}: "),
                        )

                    # Setup extra field
                    for field in parameter_fields:
                        extras = extras.replace(
                            f'{field}: {extra_parameter(parameter,f"{field}: ")}, ',
                            "",
                        )
                        extras = extras.replace(
                            f'{field}: {extra_parameter(parameter,f"{field}: ")}',
                            "",
                        )
                    extra_list = split_prompt(extras)
                    if len(extra_list) > 1:
                        for i, extra in enumerate(extra_list, 1):
                            embed.add_field(name=f"extra info {i}", value=extra, inline=False)
                    else:
                        embed.add_field(name="extra info", value=extras, inline=False)

                    # Setup other embed elements
                    embed.set_image(url=attachment.url)
                    embed.set_author(name=author_name, icon_url=author_avatar_url)
                    embed.set_footer(
                        text=f"from「{guild_name}」{channel_name}channel",
                        icon_url=guild_icon_url,
                    )

                    # Send DM
                    try:
                        await dm_channel.send(embed=embed)
                    except discord.errors.HTTPException as exception_occurred:
                        if exception_occurred.status == 400 and exception_occurred.code == 50035:
                            await dm_channel.send(
                                content=f"Infinite Magic Projection has exceeded its capacity, and Cielifra is running out of mana!\nPlease download the PNG manually and place it in the sd-webui PNG INFO tab to obtain the parameters.\nThe original link to the message is:{message_link}"
                            )
                            await message.remove_reaction(TRIGGER_REACTION, reaction_member)
                            await message.add_reaction("❎")
                        else:
                            self.log.exception("An HTTPException occurred:", exception_occurred)
                    self.log.info(_("咒文已私訊給{target}。").format(target=reaction_member.name))
            else:
                await message.remove_reaction(TRIGGER_REACTION, reaction_member)


def setup(bot: "Bot"):
    bot.add_cog(BaseEventsCog(bot))
    bot.add_cog(IMPCog(bot))
