import discord
from discord.ext import commands
from cogs.utils import checks
from cogs.utils.dataIO import dataIO
import os
from __main__ import send_cmd_help

class Guild:
    """ Guilds on Discord. Create a guild, add/remove members.
    
    Ask moderator to make a guild for you.
    As a leader you will have access to 3 commands:
    
    [p]guild add [user] - Adds a member to your guild.
    [p]guild remove [user] - Removes a member from your guild.
    [p]guild transfer [user] - Transfer leadership between guild members.

    You can also use [p]guildlist to display a list of all guilds on this server.
    
    Note: A user can be a leader only for one guild, but can be a member of many."""

    def __init__(self, bot):
        self.bot = bot
        self._settings = dataIO.load_json('data/guild/settings.json')

    def _save_settings(self):
        dataIO.save_json('data/guild/settings.json', self._settings)

    @commands.group(pass_context=True, no_pm=True)
    async def guild(self, ctx):
        """ Manage your guild. """

        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @guild.command(pass_context=True, name="add")
    async def guild_add(self, ctx, user: discord.Member=None):
        """ Add a member to your guild. """

        if user is None:
            await self.bot.send_cmd_help(ctx)
            return

        server = ctx.message.server
        author = ctx.message.author
        leader = None
        role = None

        for guild in self._settings[server.id]:
            if self._settings[server.id][guild]["Leader"] == author.id:
                leader = author
                role = discord.utils.get(server.roles, id=self._settings[server.id][guild]["Role"])
                break
        
        if leader != None:
            try:
                await self.bot.add_roles(user, role)
            except discord.errors.Forbidden:
                await self.bot.say('I don\'t have manage roles permission.')
                return
            except discord.HTTPException:
                await self.bot.say('Whoops, error.')
                return
            await self.bot.say('{} added to {}'.format(user.nick if user.nick else user.name, guild))
        else:
            await self.bot.say('You must be a leader to do that.')

    @guild.command(pass_context=True, name="remove")
    async def guild_remove(self, ctx, user: discord.Member=None):
        """ Remove a member from your guild. """

        if user is None:
            await self.bot.send_cmd_help(ctx)
            return

        server = ctx.message.server
        author = ctx.message.author
        leader = None
        role = None

        for guild in self._settings[server.id]:
            if self._settings[server.id][guild]["Leader"] == author.id:
                leader = author
                role = discord.utils.get(server.roles, id=self._settings[server.id][guild]["Role"])
                break
        
        if leader != None:
            if role in user.roles:
                try:
                    await self.bot.remove_roles(user, role)
                except discord.errors.Forbidden:
                    await self.bot.say('I don\'t have manage roles permission.')
                    return
                except discord.HTTPException:
                    await self.bot.say('Whoops, error.')
                    return
                await self.bot.say('{} removed from {}'.format(user.nick if user.nick else user.name, guild))
            else:
                await self.bot.say('This user was not in your guild in the first place :expressionless:')
        else:
            await self.bot.say('You must be a leader to do that.')


    @guild.command(pass_context=True, name="transfer")
    async def guild_transfer(self, ctx, user: discord.Member=None):
        """ Transfer your leader privileges to another member of your guild. 
        
        You must be a leader and both users must belong to the same guild."""

        if user is None:
            await self.bot.send_cmd_help(ctx)
            return

        server = ctx.message.server
        author = ctx.message.author
        leader = None
        role = None

        for guild in self._settings[server.id]:
            if self._settings[server.id][guild]["Leader"] == author.id:
                leader = author
                role = discord.utils.get(server.roles, id=self._settings[server.id][guild]["Role"])
                break
        
        if leader != None:
            if role in user.roles:
                self._settings[server.id][guild]["Leader"] = user.id
                self._save_settings()
                await self.bot.say('{} is the new leader of {}.'.format(user.nick if user.nick else user.name, guild))
            else:
                await self.bot.say('This user is not in your guild.')
        else:
            await self.bot.say('You must be a leader to do that.')



    @commands.group(pass_context=True, no_pm=True)
    async def guildset(self, ctx):
        """ Manage guilds on your server. """

        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @guildset.command(pass_context=True, name="add")
    @checks.mod_or_permissions(manage_roles=True)
    async def guildset_add(self, ctx, leader: discord.Member=None, guildname=None):
        """ Creates a guild. """

        if leader is None or guildname is None:
            await self.bot.send_cmd_help(ctx)
            return

        server = ctx.message.server

        if server.id not in self._settings:
            self._settings[server.id] = {}

        if guildname in self._settings[server.id]:
            await self.bot.say('A guild with that name already exists.')
            return

        for guild in self._settings[server.id]:
            if self._settings[server.id][guild]["Leader"] == leader.id:
                await self.bot.say('This user is already a leader for {}.'.format(guild))
                return

        #make a role and assign it to leader
        perms = discord.Permissions.none()
        try:
            role = await self.bot.create_role(server, name=guildname, permissions=perms)
            await self.bot.add_roles(leader, role)
        except discord.errors.Forbidden:
            await self.bot.say('I don\'t have manage roles permission.')
            return
        except discord.HTTPException:
            await self.bot.say('Whoops, error.')
            return


        #save to json
        self._settings[server.id][guildname] = {
            "Leader": leader.id,
            "Role": role.id
        }
        self._save_settings()
        await self.bot.say('Created guild {}.'.format(guildname))



    @guildset.command(pass_context=True, name="delete")
    @checks.mod_or_permissions(manage_roles=True)
    async def guildset_delete(self, ctx, guildname=None):
        """ Deletes a guild. """

        if guildname is None:
            await self.bot.send_cmd_help(ctx)
            return

        server = ctx.message.server

        if server.id not in self._settings or guildname not in self._settings[server.id]:
            await self.bot.say(':thinking: A guild with that name never existed...')
            return

        #remove guild role from members
        for member in server.members:
            for role in member.roles:
                if role.id == self._settings[server.id][guildname]["Role"]:
                    try:
                        await self.bot.remove_roles(member, role)
                    except discord.errors.Forbidden:
                        await self.bot.say('I don\'t have manage roles permission.')
                        return
                    except discord.HTTPException:
                        await self.bot.say('Whoops, error.')
                        return
        
        role = discord.utils.get(server.roles, id=self._settings[server.id][guildname]["Role"])
        try:
            await self.bot.delete_role(server, role)
        except discord.errors.Forbidden:
            await self.bot.say('I don\'t have manage roles permission.')
            return
        except discord.HTTPException:
            await self.bot.say('Whoops, error.')
            return

        #delete guild from json
        del(self._settings[server.id][guildname])
        self._save_settings()
        await self.bot.say('Done. Bye {}'.format(guildname))

    @commands.command(pass_context=True, no_pm=True)
    async def guildlist(self, ctx, guildname=None):
        """ Display a list of all guilds on the server.
        
        Specify [guildname] to display a list of members of this guild."""

        server = ctx.message.server

        if guildname is None:
            if server.id in self._settings:
                message = "```Guild list:\n"
                for guild in sorted(self._settings[server.id]):
                    if len(message) + len(guild) + 3 > 2000:
                        message += "```"
                        await self.bot.whisper(message)
                        message = "```\n"
                    message += "\t{}\n".format(guild)
                    #2in1 -> display all guild and all members at once
                    for member in server.members:
                        if len(message) + 32 + 3 > 2000:
                            message += "```"
                            await self.bot.whisper(message)
                            message = "```\n"
                        for role in member.roles:
                            if role.id == self._settings[server.id][guild]["Role"]:
                                message += "\t\t{}\n".format(member.nick if member.nick else member.name)
                                break
                    #end of 2in1
                if message != "```Guild list:\n":
                    message += "```"
                    await self.bot.whisper(message)
                else:
                    await self.bot.say('There are no guilds on this server.')
            else:
                await self.bot.say('There are no guilds on this server.')
            return
        else:
            if server.id in self._settings and guildname in self._settings[server.id]:
                message = "```Member list of {}:\n".format(guildname)
                for member in server.members:
                    if len(message) + len(member.nick if member.nick else member.name) + 3 > 2000:
                        await self.bot.whisper(message)
                        message="```\n"
                    for role in member.roles:
                        if self._settings[server.id][guildname]["Role"] == role.id:
                            message += "\t{}\n".format(member.nick if member.nick else member.name)
                if message != "```Member list of {}:\n".format(guildname):
                    message += "```"
                    await self.bot.whisper(message)
                else:
                    await self.bot.say('There are no members in this guild.')
            else:
                await self.bot.say('This guild doesn\'t exist in this server.')

    

def check_files():
    if not os.path.exists('data/guild/settings.json'):
        try:
            os.mkdir('data/guild')
        except FileExistsError:
            pass
        else:
            dataIO.save_json('data/guild/settings.json', {})

def setup(bot):
    check_files()
    bot.add_cog(Guild(bot))