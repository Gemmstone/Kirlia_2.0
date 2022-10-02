from ai_image.ai_image import ai_images
import discord
import re
import asyncio
import psycopg2

import httplib2
import os
import sys
import traceback
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import date, datetime
from dateutils import relativedelta

from apiclient import discovery
from apiclient import errors
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser
from oauth2client.tools import run_flow as run
import json
import urllib

from PIL import Image, ImageSequence
import random
from threading import Thread
import traceback

import requests
import wikipedia

# Discord connection

TOKEN = 'NzcwMTI1NjUxNDk0NTY3OTY2.X5ZBZw.TlsfXpDJmC1JJNQDjewVeerCs_g'
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Youtube Connection
CLIENT_SECRETS_FILE = "client_secret.json"
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

%s

with information from the Cloud Console
https://cloud.google.com/console

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

file_object = open('videos.txt', 'a')
file_object.close()
file1 = open('videos.txt', 'r')
Lines = file1.readlines()
file1.close()


def connectBD():
    con = psycopg2.connect(
        host="localhost",
            database="kirlia",
            port="5432",
            user="postgres",
            password="duarale64")
    return con


def tables(con):
    cursor = con.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS mood(id SERIAL, user_id text, scale text)")
    con.commit()
    cursor.execute("CREATE TABLE IF NOT EXISTS fechas(id SERIAL, evento text, fecha text)")
    con.commit()
    cursor.execute("CREATE TABLE IF NOT EXISTS cumples(id SERIAL, persona text, fecha text)")
    con.commit()
    cursor.execute("CREATE TABLE IF NOT EXISTS info(id SERIAL, keyword text, lugar text, informacion text)")
    con.commit()


def deleteAllD(user):
    con = connectBD()
    cursor = con.cursor()
    cursor.execute('DELETE FROM mood WHERE user_id = %s', (user,))
    con.commit()
    con.close()


def viewGraph(user):
    con = connectBD()
    cursor = con.cursor()
    cursor.execute("SELECT scale FROM mood WHERE user_id = %s", (user,))
    data = cursor.fetchall()
    con.close()
    data = list(data)[-30:]
    result = False
    for i in range(len(data)):
        result = True
        data[i] = data[i][0]
        match = re.search("Scale: (.+?) Date: ", data[i])
        if match:
            found = match.group(1)
            data[i] = int(found)
    if result:
        data.insert(0, 0)
        plt.plot(data, marker="D")
        plt.grid()
        axes = plt.gca()
        axes.set_xlim([0, len(data)-1])
        axes.set_ylim([0, 10])
        plt.xlabel("Días grabados")
        plt.ylabel("Escala de mood")
        plt.savefig('mood.png', bbox_inches='tight')
        plt.clf()
    return result


def recordData(user, value):
    con = connectBD()
    cursor = con.cursor()
    file = open("days.txt", "a+")
    file.write("Scale: " + str(value) + " Date: " + str(date.today()) + "\n")
    file.close()
    cursor.execute(
        "INSERT INTO mood(user_id, scale) VALUES (%s, %s)",
        (user, "Scale: " + str(value) + " Date: " + str(date.today()))
    )
    con.commit()
    con.close()


def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)
    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run(flow, storage)
    return discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))


def thumbnails(frames):
    size = 320, 240
    for frame in frames:
        thumbnail = frame.copy()
        thumbnail.thumbnail(size, Image.ANTIALIAS)
        yield thumbnail


def add_video_to_playlist(youtube, videoID, playlistID):

    ids = []
    playlistitems_list_request = youtube.playlistItems().list(
        playlistId=playlistID,
        part="snippet",
        maxResults=50
    )
    while playlistitems_list_request:
        playlistitems_list_response = playlistitems_list_request.execute()
        # Print information about each video.
        for playlist_item in playlistitems_list_response["items"]:
            video_id = playlist_item["snippet"]["resourceId"]["videoId"]
            ids.append(str(video_id))
        playlistitems_list_request = youtube.playlistItems().list_next(
            playlistitems_list_request, playlistitems_list_response)
    if str(videoID) not in ids:
        add_video_request = youtube.playlistItems().insert(
            part="snippet",
            body={
                'snippet': {
                    'playlistId': playlistID,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': videoID
                    }
                    # 'position': 0
                }
            }
        ).execute()
        return True
    else:
        return False


def YouTubeUrl(str):
   if "https://youtu.be/" in str or "https://www.youtube.com/" in str or "https://music.youtube.com/" in str \
           or "https://m.youtube.com/" in str:
       return True
   else:
       return False


def urltry(str):
    ur = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str)
    return ur


async def GIF_thread(lista, message):
    with urllib.request.urlopen(lista[2]) as url:
        if int(url.headers["Content-Length"]) >= 14000000 - 1:
            await message.channel.send("Archivo demasiado grande, cancelando...")
            return
        with open('temp.gif', 'wb') as f:
            f.write(url.read())
        with Image.open('temp.gif') as im:
            if im.is_animated:
                frames = [f.copy() for f in ImageSequence.Iterator(im)]
                if lista[1] == "REVERSE":
                    frames.reverse()
                elif lista[1] == "RANDOM":
                    random.shuffle(frames)
                elif lista[1] == "LOOP":
                    frames = frames + frames[::-1]
                frames[0].save('out.gif', save_all=True, format='GIF', append_images=frames[1:], loop=0, disposal=2)
                count = 0
                while Path('out.gif').stat().st_size >= 8000000 - 1:
                    im = Image.open("out.gif")
                    frames = ImageSequence.Iterator(im)
                    frames = thumbnails(frames)
                    om = next(frames)
                    om.info = im.info
                    om.save("out.gif", save_all=True, format='GIF', append_images=list(frames)[1:], loop=0, disposal=2)
                    if count == 5:
                         await message.channel.send("Archivo demasiado grande para discord")
                         return
                    count += 1
                await message.channel.send(file=discord.File('out.gif'))


async def fechas_check():
    await client.wait_until_ready()
    channel = client.get_channel(742577582347780106)
    msg_sent = False
    while True:
        hoy = datetime.now()
        tomorrow = hoy + relativedelta(days=1)
        con = connectBD()
        cursor = con.cursor()
        cursor.execute("SELECT fecha, evento FROM fechas WHERE fecha = %s or fecha = %s", (hoy.strftime("%d/%m"),
                                                                                           tomorrow.strftime("%d/%m")))
        fechas = cursor.fetchall()
        if fechas:
            if not msg_sent and hoy.hour == 7:
                for evento in fechas:
                    if evento[0] == hoy.strftime("%d/%m"):
                        await channel.send('Hoy %s es el **%s**' % (hoy.strftime("%d/%m"), evento[1]))
                    else:
                        await channel.send('Mañana %s es el **%s**' % ((hoy + relativedelta(days=1)).strftime("%d/%m"),
                                                                       evento[1]))
                msg_sent = True
        else:
            msg_sent = False
        con.close()
        await asyncio.sleep(1)


async def cumples_check():
    await client.wait_until_ready()
    channel = client.get_channel(742576032867024977)
    msg_sent = False
    server = client.get_guild(742561462953967697)
    while True:
        member_no_cumple = []
        hoy = datetime.now()
        con = connectBD()
        cursor = con.cursor()
        cursor.execute("SELECT fecha, persona FROM cumples WHERE fecha = %s", (hoy.strftime("%d/%m"),))
        cumples = cursor.fetchall()
        if cumples:
            if not msg_sent and hoy.hour == 7:
                try:
                    members = list(server.members)
                    for member in members:
                        personas = []
                        for i in range(len(cumples)):
                            personas.append(int(cumples[i][1][3:-1]))
                        if int(member.id) in personas:
                            if discord.utils.get(member.roles, name="Él") is not None \
                                    and discord.utils.get(member.roles, name="Ella") is None \
                                    and discord.utils.get(member.roles, name="Elle") is None:
                                await channel.send(
                                    'Hoy es el cumpleaños del querido %s, por favor, felicítenlo uwu' %
                                    ("<@!" + str(member.id) + ">")
                                )
                            elif discord.utils.get(member.roles, name="Ella") is not None \
                                    and discord.utils.get(member.roles, name="Él") is None \
                                    and discord.utils.get(member.roles, name="Elle") is None:
                                await channel.send(
                                    'Hoy es el cumpleaños de la querida %s, por favor, felicítenla uwu' %
                                    ("<@!" + str(member.id) + ">")
                                )
                            else:
                                await channel.send(
                                    'Hoy es el cumpleaños de le queride %s, por favor, felicítenle uwu' %
                                    ("<@!" + str(member.id) + ">")
                                )
                            try:
                                await member.add_roles(discord.utils.get(server.roles, id=770059447052926977))
                            except discord.Forbidden:
                                await client.get_channel(742577911441260567).send(
                                    "No pude darle el rol de cumpleaños a %s" % member.name
                                )
                        else:
                            member_no_cumple.append(member)
                except BaseException as error_:
                    await client.get_channel(742577911441260567).send(repr(error_))
                msg_sent = True
        else:
            msg_sent = False
            member_no_cumple = list(server.members)
        for member in member_no_cumple:
            try:
                await member.remove_roles(discord.utils.get(server.roles, id=770059447052926977))
            except discord.Forbidden:
                await client.get_channel(742577911441260567).send(
                    "No pude eliminar el rol de cumpleaños de %s" % member.name
                )
        con.close()
        await asyncio.sleep(1)


@client.event
async def on_message(message):
    try:
        if message.author == client.user or message.content.startswith('!-'):
            return
            # we do not want the bot to reply to itself

        if message.channel.id == 742573203347603628 and YouTubeUrl(message.content):
            global youtube
            enlaces = urltry(message.content)
            for enlace in enlaces:
                try:
                    videoId = str(enlace).split("=")[1].split("&")[0]
                except IndexError:
                    videoId = str(enlace).split(".be/")[1]
                added = add_video_to_playlist(get_authenticated_service(), videoId, "PLUue9qNleh81RwJzd_CWRs1lVWBkAyu9g")
                params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % videoId}
                url = "https://www.youtube.com/oembed"
                query_string = urllib.parse.urlencode(params)
                url = url + "?" + query_string
                with urllib.request.urlopen(url) as response:
                    response_text = response.read()
                    data = json.loads(response_text.decode())
                    if added:
                        await message.channel.send("Se ha añadido **%s** a la Playlist de Queerposting" %
                                                   ''.join(data['title']))
                    else:
                        await message.channel.send("**%s** ya existe en la playlist" % ''.join(data['title']))

        if message.content.startswith("!"):
            messageText = message.content[1:].upper()
            if messageText == ('HOLA'):
                msg = '¡Hola {0.author.mention}!'.format(message)
                await message.channel.send(msg)
                await message.channel.send('https://media1.tenor.com/images/c40de0b43bb905ffa233c307c4f6fd6e/tenor.gif?itemid=12329600')

            elif messageText.startswith("DI "):
                await message.channel.send(message.content[4:])
                await client.get_channel(742577911441260567).send(
                    str(message.author) + " hizo que yo dijera \"" +
                    message.content[4:] + "\" en {0.mention}".format(message.channel)
                )
                await message.delete()

            elif messageText.startswith('GIF'):
                await message.channel.send('Espera un momento, por favor...')
                lista = messageText.split(' ')
                funcion_gif = GIF_thread(lista, message)
                thread = Thread(target=await funcion_gif)
                thread.start()

            elif messageText.startswith('FECHA ') or messageText.startswith('EVENTO '):
                lista = messageText.split(' ')[1:]
                con = connectBD()
                cursor = con.cursor()
                try:
                    if lista[0] == "AÑADIR":
                        try:
                            fecha = datetime.strftime(datetime.strptime(lista[1], "%d/%m"), "%d/%m")
                            cursor.execute("SELECT fecha FROM fechas WHERE evento = %s", (" ".join(lista[2:]).title(),))
                            existencia = cursor.fetchone()
                            if existencia is None:
                                cursor.execute("INSERT INTO fechas (evento, fecha) VALUES (%s, %s)",
                                               (" ".join(lista[2:]).title(), fecha))
                                con.commit()
                                await message.channel.send('Se ha registrado el evento "**%s**" para el %s' %
                                                           (" ".join(lista[2:]).title(), fecha))
                            else:
                                await message.channel.send('Este evento ya existe, está programado para el %s' %
                                                           existencia[0])
                        except ValueError:
                            await message.channel.send('Por favor, ingresa una fecha válida en formato dd/mm')
                    elif lista[0] == "BORRAR":
                        evento = " ".join(lista[1:]).title()
                        cursor.execute("SELECT evento FROM fechas WHERE evento = %s", (evento,))
                        existencia = cursor.fetchone()
                        if existencia is not None:
                            cursor.execute("DELETE FROM fechas WHERE evento = %s", (evento,))
                            con.commit()
                            await message.channel.send('se ha eliminado el evento "**%s**"' % evento.title())
                        else:
                            await message.channel.send('No existe ningún evento llamado "%s"' % evento.title())
                    else:
                        pass
                except IndexError:
                    await message.channel.send('Por favor, ingresa una acción')
                con.commit()
                con.close()

            elif messageText.startswith('CUMPLEAÑOS ') or messageText.startswith('CUMPLE '):
                lista = messageText.split(' ')[1:]
                con = connectBD()
                cursor = con.cursor()
                try:
                    if lista[0] == "AÑADIR":
                        try:
                            fecha = datetime.strftime(datetime.strptime(lista[1], "%d/%m"), "%d/%m")
                            if lista[2].startswith("<@") and lista[2].endswith(">"):
                                cursor.execute("SELECT fecha FROM cumples WHERE persona = %s", (lista[2],))
                                existencia = cursor.fetchone()
                                if existencia is None:
                                    cursor.execute("INSERT INTO cumples (persona, fecha) VALUES (%s, %s)", (lista[2],
                                                                                                          fecha))
                                    con.commit()
                                    await message.channel.send('Se ha registrado el cumpleaños de %s para el %s' %
                                                               (lista[2], fecha))
                                else:
                                    await message.channel.send('El cumpleaños de %s ya está registrado, fecha: %s' %
                                                               (client.get_user(int(lista[2][3:-1])), existencia[0]))
                            else:
                                await message.channel.send('Por favor, menciona a un usuario')
                        except ValueError:
                            await message.channel.send('Por favor, ingresa una fecha válida en formato dd/mm')
                    elif lista[0] == "BORRAR":
                        usuario = lista[1]
                        cursor.execute("SELECT persona FROM cumples WHERE persona = %s", (usuario,))
                        existencia = cursor.fetchone()
                        if existencia is not None:
                            cursor.execute("DELETE FROM cumples WHERE persona = %s", (usuario,))
                            con.commit()
                            await message.channel.send('se ha eliminado el cumpleaños de %s' %
                                                       client.get_user(int(usuario[3:-1])))
                        else:
                            await message.channel.send('No existe ningún cumpleaños registrado a %s' %
                                                       client.get_user(int(usuario[3:-1])))
                    else:
                        pass
                except IndexError:
                    await message.channel.send('Por favor, ingresa una acción')
                con.commit()
                con.close()

            elif messageText.startswith('MTRACK'):
                lista = messageText.split(' ')
                if lista[1] == 'RESULTS' or lista[1] == 'PRIVATER':
                    result = viewGraph(message.author.id)
                    if lista[1] == "RESULTS" and result:
                        await message.channel.send('_Hugs_ {0.author.mention}, te quiero'.format(message))
                        await message.channel.send(file=discord.File('mood.png'))
                        os.remove('mood.png')
                    elif result:
                        await message.channel.send('{0.author.mention}, te he enviado tus resultados a tus DMs'.format(message))
                        await message.author.send('_Hugs_, te quiero'.format(message))
                        await message.author.send(file=discord.File('mood.png'))
                        os.remove('mood.png')
                    else:
                        await message.channel.send('No tienes datos registrados')
                elif lista[1] == 'RESET':
                    deleteAllD(message.author.id)
                    await message.channel.send('Se ha reiniciado todo tu historial')
                else:
                    try:
                        valor = int(lista[1])
                        if valor not in range(0, 11):
                            raise ValueError
                    except ValueError:
                        await message.channel.send("Por favor ingresa un número válido entre 0 y 10")
                        return
                    recordData(message.author.id, valor)
                    await message.channel.send('Nivel de mood guardado')

            elif messageText.startswith('INFO'):
                con = connectBD()
                cursor = con.cursor()
                lista = messageText.split(' ')[1:]
                if lista[0] == "AÑADIR":
                    try:
                        keyword = lista[1]
                        try:
                            lugar = lista[2]
                            try:
                                informacion = lista[3]
                                informacion = " ".join(lista[3:])
                                cursor.execute("INSERT INTO info (keyword, lugar, informacion) VALUES (%s, %s, %s)",
                                               (keyword, lugar, informacion))
                                con.commit()
                                await message.channel.send('Se ha registrado con éxito %s en %s' % (keyword, lugar))
                            except IndexError:
                                await message.channel.send('Por favor, ingresa la Información')
                        except IndexError:
                            await message.channel.send('Por favor, ingresa un **Lugar**')
                    except IndexError:
                        await message.channel.send('Por favor, ingresa una **Keyword**')
                else:
                    try:
                        keyword = lista[0]
                        cursor.execute("SELECT DISTINCT lugar FROM info WHERE keyword = %s", (keyword,))
                        lugares = cursor.fetchall()
                        if len(lugares) == 0:
                            await message.channel.send('No tengo información sobre %s', (keyword.title(),))
                        else:
                            lugar = lista[1]
                            cursor.execute("SELECT informacion FROM info WHERE keyword = %s and lugar = %s",
                                           (keyword, lugar))
                            lista_infos = cursor.fetchall()
                            if len(lista_infos) == 0:
                                await message.channel.send('No tengo datos al respecto de %s en %s', (keyword, lugar))
                                await message.channel.send('Pero tengo información en:')
                                for place in lugares:
                                    await message.channel.send('      -  **%s**' % place[0])

                            else:
                                await message.channel.send('**Tengo esta información**')
                                for i in range(len(lista_infos)):
                                    await message.channel.send('       **%s** -  %s' % (i+1, lista_infos[i][0]))

                    except IndexError:
                        await message.channel.send('Ingresa una Keyword')
                con.close()
            else:
                await message.channel.send('Perdona, este comando no lo conozco...')

        if message.content.upper().startswith("KIRLIA "):
            comando = str(message.content.upper()[7:])
            if comando.startswith("QUÉ ES ") or comando.startswith("QUé ES ") or comando.startswith("QUE ES "):
                wikipedia.set_lang("es")
                resultado = wikipedia.summary(comando[7:], sentences=2, chars=0, auto_suggest=True, redirect=True)
                await message.channel.send('**__Según Wikipedia...__**')
            elif comando.startswith("CUÁNTO ES ") or comando.startswith("CUáNTO ES ") \
                    or comando.startswith("CUANTO ES "):
                query_url = f"http://api.wolframalpha.com/v2/query?" \
                            f"appid={'4QY5GG-VTTGHU9U83'}" \
                            f"&input={urllib.parse.quote_plus(f'solve {comando[10:]}')}" \
                            f"&includepodid=Result" \
                            f"&output=json"
                r = requests.get(query_url).json()
                data = r["queryresult"]["pods"][0]["subpods"][0]
                plaintext = data["plaintext"]
                resultado = f"El resultado de **{comando[10:]}** es **{plaintext}**"
                await message.channel.send('**__Según Wolfram Alpha...__**')
            elif comando.startswith("CUÁL ES EL CLIMA EN ") or comando.startswith("CUáL ES EL CLIMA EN ") \
                    or comando.startswith("CUAL ES EL CLIMA EN ") or comando.startswith("CLIMA EN ") \
                    or comando.startswith("CLIMA "):
                api_key = "cf503c3084d42109111b70237fa75267"
                base_url = "https://api.openweathermap.org/data/2.5/weather?"
                if comando.startswith("CUÁL ES EL CLIMA EN ") or comando.startswith("CUáL ES EL CLIMA EN ") \
                        or comando.startswith("CUAL ES EL CLIMA EN "):
                    city_name = comando[20:]
                elif comando.startswith("CLIMA EN "):
                    city_name = comando[9:]
                else:
                    city_name = comando[6:]

                complete_url = base_url + "appid=" + api_key + "&q=" + city_name + "&lang=es"
                response = requests.get(complete_url)
                x = response.json()
                if x["cod"] != "404":
                    y = x["main"]
                    current_temperature = y["temp"]
                    current_humidiy = y["humidity"]
                    z = x["weather"]
                    weather_description = z[0]["description"]
                    resultado = "**Temperatura:** " + str(round(float(current_temperature) - 273.15, 2)) + \
                                "°C\n **Humedad:** " + str(current_humidiy) + "%\n _" \
                                + str(weather_description).title() + "_"
                    await message.channel.send('**__Según Open Weather...__**')
                else:
                    resultado = "No encontré esta ciudad"
            else:
                resultado = "¿Disculpa? no te entendí ):"
            await message.channel.send(resultado)

        if message.content.upper().strip() in ["SUS", "AMONG US", "AMONGUS", "AMONGAS", "AMOGUS"]:
            await message.channel.send("ඞ")
    except IndexError:
        pass
    except BaseException as error_:
        await client.get_channel(742577911441260567).send(repr(error_))
        await client.get_channel(742577911441260567).send(type(error_).__name__)
        await client.get_channel(742577911441260567).send(
            repr('An exception occurred: {}'.format(error_) + "\n\n" + traceback.format_exc())
        )


@client.event
async def on_ready():
    print('\nLogged in as %s [%s]\n' % (client.user.name, client.user.id))
    channel = client.get_channel(742577911441260567)
    await channel.send("¡Estoy en línea!")

con = connectBD()
tables(con)
con.close()

client.loop.create_task(fechas_check())
client.loop.create_task(cumples_check())
client.run(TOKEN)