import interactions
from core.ai_image_generator import ai_image
from core.imgur import image_upload, delete_file, image_resize, fsr_x2, download_image, download_attachment, archive_file
from time import perf_counter
from constants import DISCORD_TOKEN


bot = interactions.Client(token=DISCORD_TOKEN)
the_id_of_your_guild = 742561462953967697

#  ---------------------------------------------------------------------------------------------------------------------
#  --------------------------------------------- BOT FUNCTIONS ---------------------------------------------------------
#  ---------------------------------------------------------------------------------------------------------------------
pages_dic = {}


def timeout(func, args=(), kwargs={}, timeout_duration=1, default=None):
    import signal

    class TimeoutError(Exception):
        pass

    def handler(signum, frame):
        raise TimeoutError()

    # set the timeout handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_duration)
    try:
        result = func(*args, **kwargs)
    except TimeoutError as exc:
        result = default
    finally:
        signal.alarm(0)

    return result


@bot.component("inicio")
async def inicio(ctx: interactions.ComponentContext):
    if ctx.message.id in pages_dic:
        pages_dic[ctx.message.id]["current"] = 0
        buttons = [
            interactions.Button(style=interactions.ButtonStyle.SUCCESS, label='▶', custom_id="siguiente"),
            interactions.Button(style=interactions.ButtonStyle.PRIMARY, label='▶▶', custom_id="final")
        ]
        action_row = interactions.ActionRow(components=buttons)
        await ctx.message.edit(
            content="",
            embeds=[pages_dic[ctx.message.id]["pages"][pages_dic[ctx.message.id]["current"]]],
            components=[action_row]
        )
    else:
        await ctx.message.edit(
            content="Por Favor, realiza una nueva búsqueda\nLa información que has solicitado ya no está disponible",
            components=[], embeds=[]
        )


@bot.component("anterior")
async def anterior(ctx: interactions.ComponentContext):
    if ctx.message.id in pages_dic:
        buttons = []
        pages_dic[ctx.message.id]["current"] -= 1
        if pages_dic[ctx.message.id]["current"] != 0:
            buttons.append(interactions.Button(style=interactions.ButtonStyle.DANGER, label='◀◀', custom_id="inicio"))
            buttons.append(interactions.Button(style=interactions.ButtonStyle.SECONDARY, label='◀', custom_id="anterior"))
        buttons.append(interactions.Button(style=interactions.ButtonStyle.SUCCESS, label='▶', custom_id="siguiente"))
        buttons.append(interactions.Button(style=interactions.ButtonStyle.PRIMARY, label='▶▶', custom_id="final"))
        action_row = interactions.ActionRow(components=buttons)
        await ctx.message.edit(
            content="",
            embeds=[pages_dic[ctx.message.id]["pages"][pages_dic[ctx.message.id]["current"]]],
            components=[action_row]
        )
    else:
        await ctx.message.edit(
            content="Por Favor, realiza una nueva búsqueda\nLa información que has solicitado ya no está disponible",
            components=[], embeds=[]
        )


@bot.component("siguiente")
async def siguiente(ctx: interactions.ComponentContext):
    if ctx.message.id in pages_dic:
        buttons = [
            interactions.Button(style=interactions.ButtonStyle.DANGER, label='◀◀', custom_id="inicio"),
            interactions.Button(style=interactions.ButtonStyle.SECONDARY, label='◀', custom_id="anterior")
        ]
        pages_dic[ctx.message.id]["current"] += 1
        if pages_dic[ctx.message.id]["current"] < len(pages_dic[ctx.message.id]["pages"]) - 1:
            buttons.append(interactions.Button(style=interactions.ButtonStyle.SUCCESS, label='▶', custom_id="siguiente"))
            buttons.append(interactions.Button(style=interactions.ButtonStyle.PRIMARY, label='▶▶', custom_id="final"))
        action_row = interactions.ActionRow(components=buttons)
        await ctx.message.edit(
            content="",
            embeds=[pages_dic[ctx.message.id]["pages"][pages_dic[ctx.message.id]["current"]]],
            components=[action_row]
        )
    else:
        await ctx.message.edit(
            content="Por Favor, realiza una nueva búsqueda\nLa información que has solicitado ya no está disponible",
            components=[], embeds=[]
        )


@bot.component("final")
async def final(ctx: interactions.ComponentContext):
    if ctx.message.id in pages_dic:
        pages_dic[ctx.message.id]["current"] = len(pages_dic[ctx.message.id]["pages"]) - 1
        buttons = [
            interactions.Button(style=interactions.ButtonStyle.DANGER, label='◀◀', custom_id="inicio"),
            interactions.Button(style=interactions.ButtonStyle.SUCCESS, label='◀', custom_id="anterior")
        ]
        action_row = interactions.ActionRow(components=buttons)
        await ctx.message.edit(
            content="",
            embeds=[pages_dic[ctx.message.id]["pages"][pages_dic[ctx.message.id]["current"]]],
            components=[action_row]
        )
    else:
        await ctx.message.edit(
            content="Por Favor, realiza una nueva búsqueda\nLa información que has solicitado ya no está disponible",
            components=[], embeds=[]
        )


async def pages(pages_embeds, message, ctx):
    buttons = [
        interactions.Button(style=interactions.ButtonStyle.SUCCESS, label='▶', custom_id="siguiente"),
        interactions.Button(style=interactions.ButtonStyle.PRIMARY, label='▶▶', custom_id="final")
    ]
    action_row = interactions.ActionRow(components=buttons)

    pages_dic[message.id] = {
        "current": 0,
        "pages": pages_embeds,
        "author": ctx.author
    }
    await message.edit(content="", embeds=[pages_embeds[0]], components=[action_row])

#  ---------------------------------------------------------------------------------------------------------------------
#  --------------------------------------------- BOT COMMANDS ----------------------------------------------------------
#  ---------------------------------------------------------------------------------------------------------------------


@bot.command(
    name="ping",
    description="try me!",
    scope=the_id_of_your_guild,
)
async def my_first_command(ctx: interactions.CommandContext):
    await ctx.send("Pong!")

@bot.command(
    name="say",
    description="say something!",
    scope=the_id_of_your_guild,
    options=[
        interactions.Option(
            name="text",
            description="What you want to say",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def say(ctx: interactions.CommandContext, text: str):
    await ctx.send(text)


@bot.command(
    name="dalle", description="Generación de imágenes via Inteligencia Artificial", scope=the_id_of_your_guild,
    options=[interactions.Option(
        name="query", description="Qué imagen quieres generar", type=interactions.OptionType.STRING, required=True,
    )]
)
async def dalle(ctx: interactions.CommandContext, query: str):
    message = await ctx.send(f'Generando imagenes con el query:\n**___{query!r}___**')

    t1_start = perf_counter()
    files = ai_image(query)
    t1_stop = perf_counter()


    if files:
        embeds = []
        files_ = []

        await message.edit(content=f'Imágenes generadas con el query:\n**___{query!r}___**\n\n'
                                   f'Subiendo la resolución de las imágenes...')
        t2_start = perf_counter()
        files = image_resize(files)
        t2_stop = perf_counter()

        for i, file in enumerate(files):
            await message.edit(content=f'Imágenes generadas con el query:\n**___{query!r}___**\n\n'
                                       f'Generando paginación...')
            t3_start = perf_counter()
            url = image_upload(file)
            t3_stop = perf_counter()

            if url:
                embed = interactions.Embed(
                    title=f"{query!r}", url=url,
                    description=f"**Imágenes generadas en:** {t1_stop-t1_start:,.4f} segundos "
                                f"via IA con [Craiyon](https://www.craiyon.com/)\n\n"
                                f"**Imágenes escaladas en:** {t2_stop-t2_start:,.4f} segundos via **/fsr**\n"
                                f"**Imagen subida en:** {t3_stop-t3_start:,.4f} segundos a IMGUR"
                )
                embed.set_footer(f"page {i + 1}")
                embed.set_author(ctx.author.name)
                embed.set_image(url=url)
                embeds.append(embed)
            else:
                files_.append(interactions.File(file))
        if embeds:
            await pages(embeds, message, ctx)
        if files_:
            await ctx.message.reply(
                content="No se ha podido generar la paginación, enviando las fotos como archivos."
                if not embeds else
                "No se han podido paginar los siguientes archivos:",
                files=files_
            )
        for image in files:
            delete_file(image)
    else:
        await message.edit(content="No se ha podido generar la imagen, por favor, intenta de nuevo")


@bot.command(
    name="fsr", description="Supersize images", scope=the_id_of_your_guild,
    options=[
        interactions.Option(
            name="modo", description="Qué tanto más grande quieres la imagen", type=interactions.OptionType.INTEGER, required=True,
            choices=[
                interactions.Choice(name="NORMAL", value=1),
                interactions.Choice(name="ALTO", value=2),
                interactions.Choice(name="EXTREMO", value=3)]
        ),
        interactions.Option(name="imagen", description="Imagen que quieres engrandecer", type=interactions.OptionType.ATTACHMENT, required=True)
    ]
)
async def fsr(ctx: interactions.CommandContext, file: interactions.Attachment, mode: int):
    mode_name = {
        1: "NORMAL", 2: "HIGH", 3: "EXTREME"
    }
    new_size = {
        1: 2, 2: 4, 3: 8
    }
    message = await ctx.send(
        f'Aplicando FSR a la imagen:\n**___{file.filename}___**:{file.size} en el modo **{mode_name[mode]}**'
    )
    if file.size > 2000000:
        await message.edit(
            "**___DO YOU WANT TO KILL ME???!!!___**"
        )
        return
    download_attachment(await file.download(), file.filename)
    file_ = timeout(fsr_x2, args=(file.filename, mode), timeout_duration=10, default="")
    if file_ == "":
        await message.edit(
            "La imagen es demasiado grande y no hay suficiente memoria, disculpa las molestias"
        )
        delete_file(file_)
        return
    url = image_upload(file_)
    if url:
        embed = interactions.Embed(
            title=f"{file.filename!r}", url=url
        )
        embed.set_footer(mode_name[mode])
        embed.set_author(ctx.author.name)
        embed.set_image(url=url)
        await message.edit(content="", embeds=[embed])
    else:
        if file.size * new_size[mode] > 7000000:
            await message.edit(
                f"El archivo resultante es demasiado grande para enviar por discord, "
                f"disculpa las molestias\n\n"
                f"Puedes pedirle a  <@{572211944077918220}> que te lo mande por otro medio"
            )
            archive_file(f"{mode_name[mode]}_{file_}", ctx.user.username)
            return
        await ctx.message.reply(
            content=f"Se ha aplicado **FSR** a la imagen en el modo **{mode_name[mode]}**",
            files=[interactions.File(file_)]
        )
    delete_file(file_)


bot.start()
