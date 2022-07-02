# Created by RawandShaswar @ 08/06/2022, 7:00
from Classes import Dalle

# Builtin
import asyncio
import os
from pathlib import Path
from typing import Union
from PIL import Image
import random
from dotenv import load_dotenv

# Discord
import discord

# PyYaml
import yaml
from discord import Embed
from discord.ext import commands

""" Load the configuration file """
with open("data.yaml") as f:
    c = yaml.safe_load(f)


# If windows, set policy
if os.name == 'nt':
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)


def del_dir(target: Union[Path, str], only_if_empty: bool = False):
    """
    Delete a given directory and its subdirectories.

    :param target: The directory to delete
    :param only_if_empty: Raise RuntimeError if any file is found in the tree
    """
    target = Path(target).expanduser()
    if not target.is_dir():
        raise RuntimeError(f"{target} is not a directory")

    for p in sorted(target.glob('**/*'), reverse=True):
        if not p.exists():
            continue
        p.chmod(0o666)
        if p.is_dir():
            p.rmdir()
        else:
            if only_if_empty:
                raise RuntimeError(f'{p.parent} is not empty!')
            p.unlink()
    target.rmdir()


class DallEDiscordBot(commands.Bot):
    """
    Creates a discord bot.
    """

    def __init__(self, command_prefix, self_bot) -> None:
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot)
        self.add_commands()

    def create_embed(self, guild) -> Embed:
        """
        Creates an embed object.
        :param guild:
        :return:
        """
        footer = self.get_footer()

        embed = discord.Embed(title=footer[0], color=footer[2])
        embed.set_author(name="https://huggingface.co", url="https://huggingface.co/spaces/dalle-mini/dalle-mini")

        embed.set_thumbnail(url=footer[1])
        embed.set_footer(text=footer[0], icon_url=footer[1])

        return embed

    @staticmethod
    def get_footer() -> list:
        """
        Gets the footer information from the config file.
        :return:
        """
        return [c['embed_title'], c['icon_url'], c['embed_color']]

    @staticmethod
    async def on_ready() -> None:
        """
        When the bot is ready.
        :return:
        """
        print("Made with ❤️ by Rawand Ahmed Shaswar in Kurdistan")
        print("Bot is online!\nCall !dalle <query>")

    def add_commands(self) -> None:

        @self.command(name="dalle", description="Generate dall-e images using your query.")
        async def execute(ctx, *, query) -> None:
            # Check if query is empty
            if not query:
                await ctx.send("DALL·E: Invalid query\nPlease enter a query (e.g !dalle dogs on space).")
                return

            # Check if query is too long
            if len(query) > 100:
                await ctx.send("DALL·E: Invalid query\nQuery is too long.")
                return

            print(f"[-] {ctx.author} called !dalle {query}")

            await ctx.send("```DALL·E mini query: " + query + "```")
            await ctx.send("Generating images via DALL·E mini, this may take up to 2 minutes...")

            try:
                dall_e = await Dalle.DallE(prompt=f"{query}", author=f"{ctx.author.id}")
                generated = await dall_e.generate()

                if len(generated) > 0:
                    sample_image = Image.open(generated[0].path)
                    width, height = sample_image.size
                    output_image = Image.new("RGBA", (3 * width, 3 * height), (0, 0, 0, 0))
                    for i in range(len(generated)):
                        current_image = Image.open(generated[i].path)
                        for j in range(width):
                            for k in range(height):
                                current_image_pixel = current_image.getpixel((j, k))
                                output_image.putpixel(((i % 3 * width) + j, (i // 3 * height) + k), current_image_pixel)
                    filename = f'{str(random.randint(0, 9999999999))}.png'
                    output_image.save(filename)
                    file = discord.File(filename)
                    await ctx.reply(file=file)

            except Dalle.DallENoImagesReturned:
                await ctx.send(f"DALL·E mini api returned no images found for {query}.")
            except Dalle.DallENotJson:
                await ctx.send("DALL·E API Serialization Error, please try again later.")
            except Dalle.DallEParsingFailed:
                await ctx.send("DALL·E Parsing Error, please try again later.")
            except Dalle.DallESiteUnavailable:
                await ctx.send("DALL·E API Error, please try again later.")
            finally:
                # Delete the author folder in ./generated with author id, if exists
                del_dir(f"./generated/{ctx.author.id}")

        @self.command(name="ping")
        async def ping(ctx) -> None:
            """
            Pings the bot.
            :param ctx:
            :return:
            """
            await ctx.send("Pong!")

        @self.command(name="dallehelp", description="Shows the help menu.")
        async def help_command(ctx) -> None:
            """
            Displays the help command.
            :param ctx:
            :return:
            """
            await ctx.send("""
            **Commands**:
                !dallehelp - shows this message
                !ping - pong!
                !dalle <query> - makes a request to the dall-e api and returns the result
            """)


async def background_task() -> None:
    """
    Any background tasks here.
    :return:
    """
    pass

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = DallEDiscordBot(command_prefix=c['bot_prefix'], self_bot=False)
bot.loop.create_task(background_task())
bot.run(TOKEN)
