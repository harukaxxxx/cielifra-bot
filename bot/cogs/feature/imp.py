import hashlib
import random
import math
import io
import os
import json
from datetime import datetime, timezone
import discord
from PIL import Image
from bot import BaseCog, Bot, Translator, cog_i18n

_ = Translator(__name__)


async def infinite_magic_projection(self, message, payload=None):
    bot = self.bot
    guild = message.guild if message.guild is not None else message.author.id
    channel = message.channel
    reaction_member = payload.member if payload is not None else message.author
    valid_attachment = False
    for attachment in message.attachments:
        magic_id = f"{guild.id}-{channel.id}-{attachment.id}"
        magic_data = await get_magic_data(self, magic_id, attachment, message)
        if magic_data is not None:
            valid_attachment = True
            await message.add_reaction(bot.imp_reaction()["accept"])
            save_magic_data(magic_data)
            await send_DM(
                self,
                reaction_member,
                message,
                magic_id,
                magic_data,
            )

    if not valid_attachment:
        await message.remove_reaction(bot.imp_reaction()["trigger"], reaction_member)
        await message.add_reaction(bot.imp_reaction()["reject"])
        self.log.debug("IMPCog : Attachment invalid, rejected.")


async def get_magic_data(self, magic_id, attachment, message):
    # find exists magic data
    try:
        with open("logs/magics.json", "r", encoding="utf-8") as file:
            magic_dict = json.load(file)
    except FileNotFoundError:
        magic_dict = {}
    except json.decoder.JSONDecodeError:
        magic_dict = {}

    # build magic_dict
    if magic_id in magic_dict:
        self.log.info(f"Cielifra 在魔法手帳目錄找到魔法 {magic_id}，正在努力翻找手帳…")
        magic_data = {magic_id: magic_dict[magic_id]}
        self.log.debug(f"imp : magic data is {json.dumps(magic_data, indent=2)}")
        return magic_data
    elif attachment.filename.endswith(".png"):
        # check attachment is png which have parameters

        image_data = io.BytesIO(await attachment.read())
        img = Image.open(image_data)
        if "parameters" in img.info:
            parameter_info = img.info["parameters"]
            self.log.info(
                f"Cielifra 在魔法手帳目錄找不到魔法 {magic_id}，正在努力施展無限魔法投影解析魔法中…"
            )
            magic_data = await build_magic_data(self, magic_id, parameter_info, message, attachment)
            return magic_data
        elif "Software" in img.info and img.info["Software"] == "NovelAI":
            self.log.info(
                f"Cielifra 在魔法手帳目錄找不到魔法 {magic_id}，正在努力施展無限魔法投影解析魔法中…"
            )
            parameter_info = json.loads(img.info["Comment"])
            magic_data = await build_novelai_magic_data(
                self, magic_id, parameter_info, message, attachment
            )
            return magic_data
        else:
            self.log.debug("imp : Parameters info not found in image.")


async def build_magic_data(self, magic_id, parameter_info, message, attachment):
    self.log.debug("IMP Cog : Building magic data.")

    title = f"『{generate_spell(magic_id)}』"
    prompts, nprompts = get_magic_data_prompts(parameter_info)
    parameters, extra_info = get_magic_data_parameters(parameter_info)
    timestamp = datetime.now(timezone.utc).isoformat()
    author_name, author_avatar_url = await get_magic_data_author(message)
    footer_text, guild_icon_url = get_magic_data_footer(message)

    magic_data = {
        magic_id: {
            "title": title,
            "prompt": prompts,
            "nprompt": nprompts,
            "parameters": parameters,
            "extra_info": extra_info,
            "timestamp": timestamp,
            "image_url": attachment.url,
            "author": {"name": author_name, "icon_url": author_avatar_url},
            "footer": {"text": footer_text, "icon_url": guild_icon_url},
            "message_url": message.jump_url,
        }
    }
    return magic_data


async def build_novelai_magic_data(self, magic_id, parameter_info, message, attachment):
    self.log.debug("IMP Cog : Building magic data.")

    title = f"『{generate_spell(magic_id)}』"
    parameters, extra_info = get_novelai_magic_data_parameters(parameter_info)
    timestamp = datetime.now(timezone.utc).isoformat()
    author_name, author_avatar_url = await get_magic_data_author(message)
    footer_text, guild_icon_url = get_magic_data_footer(message)

    magic_data = {
        magic_id: {
            "title": title,
            "prompt": parameter_info["prompt"],
            "nprompt": parameter_info["uc"],
            "parameters": parameters,
            "extra_info": extra_info,
            "timestamp": timestamp,
            "image_url": attachment.url,
            "author": {"name": author_name, "icon_url": author_avatar_url},
            "footer": {"text": footer_text, "icon_url": guild_icon_url},
            "message_url": message.jump_url,
        }
    }
    return magic_data


def generate_spell(input_text):
    magic_spells = [
        "⚡✨Zephyrus Alakazamia✨⚡",
        "🌟✨Lumina Seraphicus✨🌟",
        "🌌🌟Astra Eternus🌟🌌",
        "🌙✨Mysticus Vorpalus✨🌙",
        "🔥✨Solarius Incantatio✨🔥",
        "🌪️✨Aquilo Spiralis✨🌪️",
        "🐉🔥Ignis Draconis🔥🐉",
        "🌿🌳Veridia Arborum🌳🌿",
        "🌌⭐Celestis Mirabilis⭐🌌",
        "🌑🌙Umbra Nocturna🌙🌑",
        "✨⚡Divinus Fulgor⚡✨",
        "🌧️🌊Tempestas Fluvius🌊🌧️",
        "🌍🌱Terra Vitalis🌱🌍",
        "🦅✨Volatus Levitas✨🦅",
        "🔮✨Arcanus Omnipotens✨🔮",
        "💜✨Amethysta Magica✨💜",
        "🛡️✨Fortis Protego✨🛡️",
        "❓🌌Enigma Invisus🌌❓",
        "⚔️🌌Bellum Caelum🌌⚔️",
        "🌳🌿Sylva Perpetua🌿🌳",
        "🔥🌌Flamara Infernalis🌌🔥",
        "✨🌌Aetherius Radiance🌌✨",
        "🌐🔗Meridianus Nexus🔗🌐",
        "🌈🌌Spectra Illusionis🌌🌈",
        "🌌🔮Nexus Portentia🔮🌌",
        "🕊️🌬️Volucris Velocitas🌬️🕊️",
        "🔮🌌Mirus Transmutatio🌌🔮",
        "⚡✨Fulgurante Lumine✨⚡",
        "🌺🌟Harmonia Elysium🌟🌺",
        "🌌✨Luminara Effervescens✨🌌",
        "🌸✨Flora Viventia✨🌸",
        "🔥🌪️Ignis Turbinis🌪️🔥",
        "🌟🌌Stellae Infinitas🌌🌟",
        "⚡🌊Fulgor Aqua🌊⚡",
        "🌑🦉Umbra Noctua🦉🌑",
        "🌞🌙Lux Lunaris🌙🌞",
        "🍃✨Aura Vitalis✨🍃",
        "🔮🌌Magia Arcana🌌🔮",
        "🌹✨Rosaceus Lumina✨🌹",
        "🌌🗝️Cosmos Clavis🗝️🌌",
        "🌪️🌊Tempestas Mare🌊🌪️",
        "🔥⚔️Ignis Gladius⚔️🔥",
        "🌈🔮Iris Divinatio🔮🌈",
        "💫✨Siderea Splendor✨💫",
        "🌙🦋Noctis Papilio🦋🌙",
        "🔥🌿Ignis Herba🌿🔥",
        "⚡🌪️Fulgur Turbo🌪️⚡",
        "🌌✨Astrum Luminis✨🌌",
        "🌺🌊Flora Maris🌊🌺",
        "🌙🔮Luna Divinatrix🔮🌙",
        "🌟🌿Stella Viridis🌿🌟",
    ]

    # Convert to MD5 hash value
    md5_hash = hashlib.md5(input_text.encode()).hexdigest()

    # Convert MD5 hash value to integer
    hash_int = int(md5_hash, 16)

    # Randomly choose a spell
    random.seed(hash_int)
    random_spell = random.choice(magic_spells)

    return random_spell


def get_magic_data_prompts(parameter_info):
    nprompt_index = parameter_info.find("Negative prompt: ")
    steps_index = parameter_info.find("Steps: ")
    prompts = parameter_info[0:nprompt_index]
    nprompts = parameter_info[nprompt_index + 17 : steps_index]
    return prompts, nprompts


def get_magic_data_parameters(parameter_info: str):
    steps_index = parameter_info.find("Steps: ")
    parameter_string = parameter_info[steps_index - 1 : len(parameter_info)]

    # create parameter dict from string
    parameter_pairs = parameter_string.split(',')
    merge_book = []
    for k, pair in enumerate(parameter_pairs):
        if '"' in pair and pair.count('"') == 1:
            merge_book.append(k)
    merged_parameters = merge_parameters(parameter_pairs, merge_book)
    parameter_dict = create_dict_from_parameter_pairs(merged_parameters)

    parameters = {
        "Steps": parameter_dict["Steps"],
        "CFG scale": parameter_dict["CFG scale"],
        "Seed": parameter_dict["Seed"],
        "Sampler": parameter_dict["Sampler"],
        "Model": f"{parameter_dict['Model']} [{parameter_dict['Model hash']}]",
        "VAE": f"{parameter_dict['VAE']} [{parameter_dict['VAE hash']}]",
        "Size": parameter_dict["Size"],
        "Version": parameter_dict["Version"],
    }

    if "Hires upscale" in parameter_dict:
        hires_parameters = ["Hires upscale", "Hires steps", "Hires upscaler", "Denoising strength"]
        for lora_hashes in hires_parameters:
            if lora_hashes in parameter_dict:
                parameters.update({lora_hashes: parameter_dict[lora_hashes]})
            else:
                parameters.update({lora_hashes: "-"})

    # add extra hashes
    extra_hashes = ["Lora hashes", "Lyco hashes", "TI hashes"]
    for hashes in extra_hashes:
        if hashes in parameter_dict:
            lora_hashes_string = parameter_dict[hashes].replace('"', "")
            lora_hashes_dict = create_dict_from_parameter_pairs(lora_hashes_string.split(','))
            lora_hashes = ""
            for k, v in lora_hashes_dict.items():
                lora_hashes += f"{k} [{v}]\n"
            parameters.update({hashes: lora_hashes})

    # collecting extra_parameters
    extra_parameters_dict = {
        key: value for key, value in parameter_dict.items() if key not in parameters
    }
    extra_parameters_dict.pop("Model hash")
    extra_parameters_dict.pop("VAE hash")

    extra_parameters = ", ".join(
        [f"{key}: {value}" for key, value in extra_parameters_dict.items()]
    )

    return parameters, extra_parameters


def get_novelai_magic_data_parameters(parameter_info: str):
    parameters = {
        "Steps": str(parameter_info["steps"]),
        "CFG scale": str(parameter_info["scale"]),
        "Seed": str(parameter_info["seed"]),
        "Sampler": parameter_info["sampler"],
        "Model": "NovelAI",
        "Size": f"{parameter_info['height']}x{parameter_info['width']}",
    }

    used_parameters = ["prompt", "uc", "steps", "scale", "seed", "sampler", "height", "width"]

    extra_info = ""
    for key, value in parameter_info.items():
        if key not in used_parameters:
            extra_info += f"{key}: {value}, "

    return parameters, extra_info


async def get_magic_data_author(message):
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
    return author_name, author_avatar_url


def get_magic_data_footer(message):
    guild = message.guild
    guild_name = guild.name
    channel = message.channel
    channel_name = channel.name
    footer_text = f"來自「{guild_name}」{channel_name}頻道"
    guild_icon_url = (
        guild.icon.url
        if guild.icon is not None
        else f"https://fakeimg.pl/300x300/?text={guild_name[0]}"
    )
    return footer_text, guild_icon_url


def save_magic_data(magic_data):
    file_path = "logs/magics.json"

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump({}, file)
    with open(file_path, "r", encoding="utf-8") as file:
        existing_magic_data = json.load(file)

    for magic_data_id, data in magic_data.items():
        existing_magic_data[magic_data_id] = data

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(existing_magic_data, file, ensure_ascii=False, indent=2)


async def send_DM(
    self,
    reaction_member,
    message,
    magic_id,
    magic_data,
):
    bot = self.bot
    embed_fields = build_embed_fields(magic_id, magic_data)
    embed_dict = build_embed_dict(magic_id, magic_data, embed_fields)
    magic_embed = discord.Embed.from_dict(embed_dict)
    dm_channel = await reaction_member.create_dm()
    try:
        await dm_channel.send(embed=magic_embed)
    except discord.errors.HTTPException as exception_occurred:
        if exception_occurred.status == 400 and exception_occurred.code == 50035:
            await dm_channel.send(
                content=_(
                    "無限魔法投影已超出負荷，Cielifra 的法力正在耗盡！\n請手動下載 PNG 使用 sd-webui 的 PNG info 功能獲取咒文。\n原始訊息的連結是：{message_url}"
                ).format(message_url=embed_dict["url"])
            )
            await message.remove_reaction(bot.imp_reaction()["trigger"], reaction_member)
        else:
            self.log.exception("發生了一個 HTTP 例外：", exception_occurred)
    self.log.info(f"Cielifra 成功將魔法 {magic_id} 的咒文私訊給 {reaction_member.name}了。")


def build_embed_fields(magic_id, magic_data):
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
        name = f"Negative Prompt {i}" if len(nprompt_list) > 1 else "Negative Prompt"
        nprompt_fields.append(
            {
                "name": name,
                "value": parameter,
            }
        )
    embed_fields.extend(nprompt_fields)

    # add parameter fields
    parameter_field = [{"name": "Parameters", "value": ""}]
    inline = True
    for parameter, value in magic_data[magic_id]["parameters"].items():
        # add title
        if parameter == "Hires upscale":
            parameter_field.append({"name": "Hires info", "value": ""})
        if "hashes" in parameter:
            inline = False

        parameter_dict = {
            "name": parameter,
            "value": value,
            "inline": inline,
        }

        parameter_field.append(parameter_dict)

    embed_fields.extend(parameter_field)

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
    return embed_fields


def build_embed_dict(magic_id, magic_data, embed_fields):
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
    return embed_dict


def merge_parameters(parameter_string_pairs, merge_book):
    merged_parameters = []
    skip_until = -1
    for k, pair in enumerate(parameter_string_pairs):
        if k < skip_until:
            continue
        if k in merge_book:
            # Find the end index from merge_book
            end_index = merge_book[merge_book.index(k) + 1]
            # Concatenate the strings from start to end index
            merged_pair = ','.join(parameter_string_pairs[k : end_index + 1])
            merged_parameters.append(merged_pair)
            skip_until = end_index + 1
        else:
            merged_parameters.append(pair)
    return merged_parameters


def create_dict_from_parameter_pairs(merged_parameters):
    parameters_dict = {}
    for param in merged_parameters:
        if ':' in param:
            key, value = param.split(':', 1)  # Split only on the first colon
            parameters_dict[key.strip()] = value.strip()
    return parameters_dict


def split_parameter(parameter):
    if len(parameter) > 1024:
        parts = parameter.split(",")
        result_list = []
        temp = ""

        slice_num = len(parameter) / math.ceil(len(parameter) / 1024)
        if slice_num * 1.1 >= 1024:
            slice_num = 1024
        else:
            slice_num = slice_num * 1.1

        for part in parts:
            if len(temp) + len(part) <= slice_num:
                temp += part + ","
            else:
                result_list.append(temp)
                temp = part + ","
        if temp:
            result_list.append(temp)
    else:
        result_list = [parameter]

    return result_list


@cog_i18n
class IMPCog(BaseCog, name="咒文讀取"):
    @discord.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        bot = self.bot
        if payload.emoji.name == bot.imp_reaction()["trigger"]:
            channel = await bot.get_or_fetch_channel(payload.channel_id)
            message = await channel.fetch_message(int(payload.message_id))
            reaction_member = payload.member if payload is not None else message.author

            if message.attachments:
                await infinite_magic_projection(self, message, payload)
            else:
                await message.remove_reaction(bot.imp_reaction()["trigger"], reaction_member)
                self.log.debug(
                    "IMPCog : Message doesn't have attachments, removed trigger reaction."
                )


def setup(bot: "Bot"):
    bot.add_cog(IMPCog(bot))
