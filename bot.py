import asyncio
import datetime
import gettext
import os

import coc
import discord


t = gettext.translation('bot', 'locale', languages=['ko'], fallback=True)
_ = t.gettext


print(_('Logging in to COC API...'))

email = os.getenv('COC_BOT_EMAIL')
password = os.getenv('COC_BOT_PASSWORD')
coc_client = coc.login(email, password, client=coc.EventsClient)

clan_tag = '#U8YJLRQU'
members_last_updated = {}

recently_notified_war_clans = set()


dc_bot_token = os.getenv('DISCORD_BOT_TOKEN')
dc_client = discord.Client()

topology_id = 653614701476839450
general_id = 653614701476839453


async def wait_until_ready():
    while not dc_client.is_ready():
        await asyncio.sleep(60)


async def send_message(guild_id, channel_id, message):
    await wait_until_ready()
    channel = dc_client.get_guild(guild_id).get_channel(channel_id)
    await channel.send(message)


@coc_client.event
async def on_clan_member_join(member, clan):
    await send_message(topology_id, general_id, _('{} joined the clan! :tada:').format(member.name))


@coc_client.event
async def on_clan_member_leave(member, clan):
    await send_message(topology_id, general_id, _('{} left the clan.').format(member.name))


async def watch_clan_war(timeout=600):
    # Check for regular clan war
    clan_war = await coc_client.get_clan_war(clan_tag)
    if clan_war.status != 'inWar':
        # Check for league war
        league_group = await coc_client.get_league_group(clan_tag)
        war_coro = []
        for war_round in league_group.rounds:
            for war_id in war_round:
                if war_id != '#0':
                    war_coro.append(coc_client.get_league_war(war_id))
        war_list = await asyncio.gather(*war_coro)
        for war in war_list:
            if war.state == 'inWar':
                if war.clan.tag == clan_tag or war.opponent.tag == clan_tag:
                    clan_war = war
                    break
        else:
            # Currently not in war
            await asyncio.sleep(timeout)
            await watch_clan_war(timeout)

    now = datetime.datetime.utcnow()
    war_end = clan_war.end_time.time

    global recently_notified_war_clans
    war_clans = {clan_war.clan.tag, clan_war.opponent.tag}

    if war_end - now < datetime.timedelta(hours=1):
        if recently_notified_war_clans != war_clans:
            recently_notified_war_clans = war_clans
            await send_message(topology_id, general_id, _('Clan war is less than an hour left! :rocket:'))

    await asyncio.sleep(timeout)
    await watch_clan_war(timeout)


def main():
    print(_('Fetching clan data...'))
    loop = asyncio.get_event_loop()
    clan = loop.run_until_complete(coc_client.get_clan(clan_tag))

    print(_('Logging in to Discord API...'))

    loop.run_until_complete(dc_client.login(dc_bot_token))
    asyncio.ensure_future(dc_client.connect())

    global members_last_updated
    members_last_updated = {player.tag: datetime.datetime.now() for player in clan.members}

    coc_client.add_clan_update(clan_tag)
    asyncio.ensure_future(watch_clan_war())

    print(_('Initialization complete! Starting the bot...'))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(dc_client.logout())
        loop.run_until_complete(coc_client.http.close())
        loop.close()


if __name__ == '__main__':
    main()
