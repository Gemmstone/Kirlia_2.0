import interactions
from constants import DEEP_AI_KEY, OPEN_AI_KEY
from core.ai_image_generator import ai_image, stability_ai_image
from core.imgur import image_upload, delete_file, image_resize, fsr_x2, download_image, \
    download_attachment, archive_file, combine_pictures, chunkIt, archive_file_dalle
from time import perf_counter
from constants import DISCORD_TOKEN, OPEN_WEATHER_KEY, SCOPE
import wikipedia
import urllib
import traceback
import requests
import json


bot = interactions.Client(token=DISCORD_TOKEN)

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


@bot.component("fsr_dalle_1")
@bot.component("fsr_dalle_2")
@bot.component("fsr_dalle_3")
@bot.component("fsr_dalle_4")
@bot.component("fsr_dalle_5")
@bot.component("fsr_dalle_6")
@bot.component("fsr_dalle_7")
@bot.component("fsr_dalle_8")
@bot.component("fsr_dalle_9")
async def fsr_dalle(ctx: interactions.ComponentContext):
    file = f"./ArchiveDalle/{ctx.message.id}/{ctx.custom_id.split('_')[-1]}.jpg"
    message = await ctx.send(f'Aplicando FSR a la imagen: **___{ctx.custom_id.split("_")[-1]}___**')

    file_ = fsr_x2(file, replace=False, times=3)
    url = image_upload(file_)
    if url:
        embed = interactions.Embed(
            title=f"Imagen {ctx.custom_id.split('_')[-1]}, Engrandecida", url=url
        )
        embed.set_author(ctx.author.name)
        embed.set_image(url=url)
        await message.edit(content="", embeds=[embed])
    else:
        await ctx.message.reply(
            content=f"Se ha aplicado **FSR** a la imagen **{ctx.custom_id.split('_')[-1]}**",
            files=[interactions.File(file_)]
        )
    delete_file(file_)


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


async def wikisearch(ctx, message, query):
    wikipedia.set_lang("es")
    try:
        options = []
        try:
            page = wikipedia.page(query.title())
        except wikipedia.exceptions.DisambiguationError as error:
            options = error.options
            page = wikipedia.page(options[0])
            options = options[1:]
        except wikipedia.exceptions.PageError:
            await message.edit(f"No he encontrado nada con el nombre **__'{query}'__**, por favor, intenta otro query")
            return

        embed = interactions.Embed(
            title=page.title, url=page.url,
            description=wikipedia.summary(page.title, sentences=2, chars=0, auto_suggest=True, redirect=True)
        )
        embed.set_footer(f"Preguntado por: {ctx.author.name}")
        embed.set_author("Según Wikipedia:")

        if options:
            embed.add_field("Quizá quisiste decir:", "\n".join(options), True)

        images = [i for i in page.images if i.endswith('.jpg')]
        if images:
            embed.set_thumbnail(url=images[0])

        await message.edit("", embeds=[embed])
    except BaseException as error:
        print(error)
        error_embed = interactions.Embed(
            title=type(error).__name__,
            description=repr('An exception occurred: {}'.format(error) + "<br><br>" + traceback.format_exc())
        )
        error_embed.set_author(repr(error))
        error_embed.set_footer(f"Error buscando: {query}")
        await message.edit("¡Ha ocurrido un error!", embeds=[error_embed])


def deg_to_text(deg):
    return [
        "Norte",
        "Norte-Noreste",
        "Noreste",
        "Este-Noreste",
        "Este",
        "Este-Sureste",
        "Sureste",
        "Sur-Sureste",
        "Sur",
        "Sur-Suroeste",
        "Suroeste",
        "Oeste-Suroeste",
        "Oeste",
        "Oeste-Noroeste",
        "Noroeste",
        "Norte-Noroeste"
    ][
        round(deg/22.5)%16
    ]

#  ---------------------------------------------------------------------------------------------------------------------
#  --------------------------------------------- BOT COMMANDS ----------------------------------------------------------
#  ---------------------------------------------------------------------------------------------------------------------


@bot.command(
    name="hola",
    description="try me!",
    scope=SCOPE,
)
async def my_first_command(ctx: interactions.CommandContext):
    await ctx.send(f'¡Hola {ctx.author.mention}!')
    await ctx.channel.send('https://media1.tenor.com/images/c40de0b43bb905ffa233c307c4f6fd6e/tenor.gif?itemid=12329600')


@bot.command(
    name="di",
    description="say something!",
    scope=SCOPE,
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
    name="open_ai",
    description="say something!",
    scope=SCOPE,
    options=[
        interactions.Option(
            name="text",
            description="What you want to say",
            type=interactions.OptionType.STRING,
            required=True,
        ),
    ],
)
async def open_ai(ctx: interactions.CommandContext, text: str):
    message = await ctx.send(f"Generando texto usando **{text!r}** como semilla")

    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers={'Authorization': f'Bearer {OPEN_AI_KEY}'},
        json={
            'model': 'text-davinci-002',
            'prompt': text,
            'temperature': 1,
            'max_tokens': 4000,
        }
    )

    embeds = []
    for i in json.loads(response.text)["choices"]:
        embed = interactions.Embed(title=text.title(), description=i["text"])
        embed.set_author("Hecho con OpenAI")
        embed.set_footer(f"Solicitado por: {ctx.author.name}")
        embeds.append(embed)
    await message.edit("", embeds=embeds)


@bot.command(
    name="imagina", description="Generación de imágenes via Inteligencia Artificial", scope=SCOPE,
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
        groups = []
        for i, group in enumerate(chunkIt(files)):
            groups.append(combine_pictures(group, filename=f"combined_pictures_{i}.jpg"))
        combined_file = combine_pictures(groups, orientation=False, delete_files=True)
        t3_start = perf_counter()
        url = image_upload(combined_file)
        t3_stop = perf_counter()

        buttons = []
        for i, picture in enumerate(files):
            buttons.append(
                interactions.Button(
                    style=interactions.ButtonStyle.SECONDARY,
                    label=f"{i+1}",
                    custom_id=f"fsr_dalle_{i+1}"
                )
            )

        action_rows = []
        for group in chunkIt(buttons):
            action_rows.append(interactions.ActionRow(components=group))

        if url:
            embed = interactions.Embed(
                title=f"{query!r}", url=url,
                description=f"**Imágenes generadas en:**\n{t1_stop - t1_start:,.4f} segundos "
                            f"via IA con [Craiyon](https://www.craiyon.com/)\n\n"
                            f"**Imagen subida en:**\n{t3_stop - t3_start:,.4f} segundos a IMGUR"
            )
            embed.set_footer(f"Selecciona la imagen que quieres ver en grande:")
            embed.set_author(ctx.author.name)
            embed.set_image(url=url)
            await message.edit(content="", embeds=[embed], components=action_rows)
        else:
            message = await ctx.message.reply(
                content=f"Aquí tienes los resultados de {query!r}, selecciona abajo cuál quieres ver en grande.",
                files=[interactions.File(combined_file)],   # files_
                components=action_rows
            )
        for i, file in enumerate(files):
            archive_file_dalle(file, f"{message.id}", i+1)
        delete_file(combined_file)
    else:
        await message.edit(content="No se ha podido generar la imagen, por favor, intenta de nuevo")


@bot.command(
    name="dream", description="Generación de imágenes via Inteligencia Artificial", scope=SCOPE,
    options=[interactions.Option(
        name="query", description="Qué imagen quieres generar", type=interactions.OptionType.STRING, required=True,
    )]
)
async def dream(ctx: interactions.CommandContext, query: str):
    message = await ctx.send(f'Generando imagen con el query:\n**___{query!r}___**')

    t1_start = perf_counter()
    files = stability_ai_image(query)
    t1_stop = perf_counter()
    print(t1_start - t1_stop)


@bot.command(
    name="fsr", description="Supersize images", scope=SCOPE,
    options=[
        interactions.Option(
            name="modo", description="Qué tanto más grande quieres la imagen", type=interactions.OptionType.INTEGER,
            required=True,
            choices=[
                interactions.Choice(name="NORMAL", value=1),
                interactions.Choice(name="ALTO", value=2),
                interactions.Choice(name="EXTREMO", value=3)]
        ),
        interactions.Option(name="imagen", description="Imagen que quieres engrandecer",
                            type=interactions.OptionType.ATTACHMENT, required=True)
    ]
)
async def fsr(ctx: interactions.CommandContext, file: interactions.Attachment, mode: int):
    mode_name = {
        1: "NORMAL", 2: "ALTO", 3: "EXTREMO"
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


@bot.command(
    name="explica",
    description="Busqueda en wikipedia!",
    scope=SCOPE,
    options=[
        interactions.Option(
            name="busqueda",
            description="Lo que quieres buscar",
            type=interactions.OptionType.STRING,
            required=True
        ),
    ],
)
async def wiki(ctx: interactions.CommandContext, query: str):
    message = await ctx.send(f"Buscando **__*{query}*__**...")
    await wikisearch(ctx, message, query)


@bot.command(
    name="curiosidad",
    description="Busqueda en wikipedia aleatoria!",
    scope=SCOPE,
)
async def wiki_random(ctx: interactions.CommandContext):
    wikipedia.set_lang("es")
    query = wikipedia.random(pages=1)
    message = await ctx.send(f"Buscando **__*¡¡¡RANDOM!!!*__**...")
    await wikisearch(ctx, message, query)


@bot.command(
    name="calculadora",
    description="Una calculadora muy inteligente",
    scope=SCOPE,
    options=[
        interactions.Option(
            name="expresion",
            description="Lo que quieres calcular",
            type=interactions.OptionType.STRING,
            required=True
        ),
    ],
)
async def wolframalpha(ctx: interactions.CommandContext, expression: str):
    message = await ctx.send(f"Calculando **__*{expression}*__**...")

    query_url = f"http://api.wolframalpha.com/v2/query?" \
                f"appid={'4QY5GG-VTTGHU9U83'}" \
                f"&input={urllib.parse.quote_plus(f'solve {expression}')}" \
                f"&includepodid=Result" \
                f"&output=json"

    embed = interactions.Embed(
        title=requests.get(query_url).json()["queryresult"]["pods"][0]["subpods"][0]["plaintext"],
        description="Según Wolfram Alpha"
    )
    embed.set_author(f"{expression} =")
    embed.set_footer(f"Preguntado por: {ctx.author.name}")
    await message.edit('', embeds=[embed])


@bot.command(
    name="clima",
    description="pregunta cómo está el clima en una ciudad",
    scope=SCOPE,
    options=[
        interactions.Option(
            name="ciudad",
            description="El clima de la ciudad que quieres consultar",
            type=interactions.OptionType.STRING,
            required=True
        ),
    ],
)
async def clima(ctx: interactions.CommandContext, ciudad: str):
    message = await ctx.send(f"Buscando el clima en **__*{ciudad}*__**...")
    if ciudad.lower() == "jalapa":
        ciudad = "jalapa, gt"
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?appid={OPEN_WEATHER_KEY}&q={ciudad}&lang=es"
    ).json()

    if response["cod"] == 200:
        main = response['main']
        weather = response['weather'][0]
        wind = response['wind']
        visibility = response['visibility']
        clouds = response['clouds']
        sys = response['sys']

        embed = interactions.Embed(
            title=weather["description"].title(),
            description=f"{response['name']}, {response['sys']['country']}"
        )
        embed.set_thumbnail(url=f'http://openweathermap.org/img/wn/{weather["icon"]}.png')

        embed.add_field("Temperatura:", f"{round(float(main['temp']) - 273.15, 2)}°C", False)

        embed.add_field("Temp. Minima:", f"{round(float(main['temp_min']) - 273.15, 2)}°C", True)
        embed.add_field("Temp. Máxima:", f"Max: {round(float(main['temp_max']) - 273.15, 2)}°C", True)
        embed.add_field("Sensación:", f"{round(float(main['feels_like']) - 273.15, 2)}°C", True)

        embed.add_field("Humedad:", f'{main["humidity"]}%', True)
        embed.add_field("Presión:", f'{main["pressure"]}hPa', True)
        embed.add_field("Nubes:", f'{clouds["all"]}%', True)
        embed.add_field("Visibilidad:", f"{visibility / 1000}km", True)
        embed.add_field("Velocidad del Viento:", f'{wind["speed"]}m/s', True)
        embed.add_field("Dirección del Viento:", deg_to_text(wind["deg"]), True)

        embed.set_author(f"Según OpenWeather:")
        embed.set_footer(f"{response['coord']['lon']}, {response['coord']['lat']}")
        await message.edit('', embeds=[embed])
    else:
        await message.edit(f'Ha ocurrido un problema (_{response["cod"]}_) buscando la ciudad **{ciudad}**')


bot.start()
