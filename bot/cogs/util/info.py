from datetime import datetime, timedelta

import discord
from discord import Embed

from bot import ApplicationContext, BaseCog, Bot, Translator, cog_i18n

_ = Translator(__name__)


@cog_i18n
class InfoCog(BaseCog, name="雜項"):
    @discord.slash_command(
        guild_only=True,
        i18n_name=_("上線時間"),
        i18n_description=_("查看機器人上線時間"),
    )
    async def uptime(self, ctx: ApplicationContext):
        uptime: timedelta = datetime.now() - self.bot.uptime

        s = int(uptime.total_seconds())
        days, remainder = divmod(s, (h_s := (s_s := 60) ** 2) * 24)
        hours, remainder = divmod(remainder, h_s)
        minutes, seconds = divmod(remainder, s_s)

        embed = Embed(
            title=ctx._("機器人上線時間"),
            description=ctx._("{days:02d}天 {hours:02d}小時 {minutes:02d}分鐘 {seconds:02d}秒").format(
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds,
            ),
        )

        await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(
        guild_only=False,
        i18n_name=_("邀請連結"),
        i18n_description=_("生成機器人邀請連結"),
    )
    async def invite(self, ctx: ApplicationContext):
        bot = self.bot

        await ctx.respond(
            _("機器人邀請連結：{invite_url}").format(
                invite_url=discord.utils.oauth_url(
                    client_id=bot.application_id,
                    permissions=discord.Permissions(permissions=2419452944),
                )
            )
        )


def setup(bot: "Bot"):
    bot.add_cog(InfoCog(bot))
