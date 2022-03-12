# coding=utf-8
#!/usr/bin/env python3

from asyncio.base_subprocess import WriteSubprocessPipeProto
# from ctypes import WinDLL
# from pty import fork
import socket
import selectors    #https://docs.python.org/3/library/selectors.html
import select
from ssl import SOL_SOCKET
import types        # Para definir el tipo de datos data
import argparse     # Leer parametros de ejecución
import os           # Obtener ruta y extension
from datetime import datetime, timedelta # Fechas de los mensajes HTTP
import time         # Timeout conexión
import sys          # sys.exit
import re           # Analizador sintáctico
import logging
from unittest import result      # Para imprimir logs


BUFSIZE = 8192 # Tamaño máximo del buffer que se puede utilizar
TIMEOUT_CONNECTION = 20 # Timout para la conexión persistente
MAX_ACCESOS = 10
CODIGO_RESPUESTA = "200"
MAX_AGE = "120"
KEEP_ALIVE_TIME = TIMEOUT_CONNECTION+1

patron_solicitud = r"\b(GET|POST|HEAD|PUT|DELETE) (/.*) HTTP/(\d\.\d)$"
er_solicitud = re.compile(patron_solicitud)

# Extensiones admitidas (extension, name in HTTP)
filetypes = {"gif":"image/gif", "jpg":"image/jpg", "jpeg":"image/jpeg", "png":"image/png", "htm":"text/htm", 
             "html":"text/html", "css":"text/css", "js":"text/js"}

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s.%(msecs)03d] [%(levelname)-7s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()


def enviar_mensaje(cs, data):
    """ Esta función envía datos (data) a través del socket cs
        Devuelve el número de bytes enviados.
    """
    return cs.send(data)


def recibir_mensaje(cs):
    """ Esta función recibe datos a través del socket cs
        Leemos la información que nos llega. recv() devuelve un string con los datos.
    """
    return cs.recv(BUFSIZE).decode()


def cerrar_conexion(cs):
    """ Esta función cierra una conexión activa.
    """
    cs.close()

def process_cookies(headers):
    """ Esta función procesa la cookie cookie_counter
        1. Se analizan las cabeceras en headers para buscar la cabecera Cookie
        2. Una vez encontrada una cabecera Cookie se comprueba si el valor es cookie_counter
        3. Si no se encuentra cookie_counter , se devuelve 1
        4. Si se encuentra y tiene el valor MAX_ACCESSOS se devuelve MAX_ACCESOS
        5. Si se encuentra y tiene un valor 1 <= x < MAX_ACCESOS se incrementa en 1 y se devuelve el valor
    """
    cabeceraCookie = "Cookie"
    cabeceraSolucion = ""

    #Cookie: cookie_counter=3

    for c in headers:
        if (c.startswith(cabeceraCookie)):
            cabeceraSolucion = c

    if cabeceraSolucion == "":
        return 1
    else:
        cabeceraMod = cabeceraSolucion.replace(" ","")
        splittedCookie = cabeceraMod.split(":")
        cookie_counter = splittedCookie[1]
        counter = cookie_counter.split("=")[1]
        if (int(counter)==MAX_ACCESOS):
            return MAX_ACCESOS
        elif (int(counter)>=1 and int(counter)<=MAX_ACCESOS):
            return int(counter)+1
        return 1

def devolver400(cs, webroot):
    error400 = "HTTP/1.1 400 Bad Request\r\n"
    error400 = error400 + "Date: "
    error400 = error400 + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') +"\r\n"
    error400 = error400 + "Server: web.kaorisite.org\r\n"
    error400 = error400 + "Connection: "
    error400 = error400 + "keep-alive\r\n"
    error400 = error400 + "Keep-Alive: timeout = " + str(KEEP_ALIVE_TIME) + "\r\n"
    error400 = error400 + "Content-Length: "
    url = webroot + "/Error400.html"
    tamanoerror = os.stat(url).st_size
    ext = "html"
    error400 = error400 + str(tamanoerror) + "\r\n"
    error400 = error400 + "Content-Type: "
    error400 = error400 + filetypes[ext] + "\r\n\r\n"
    
    f = open(url, 'rb', BUFSIZE)
    texto = f.read(tamanoerror)
    encoded_error = error400.encode()
    mensaje_error = encoded_error + texto
    f.close()

    enviar_mensaje(cs, mensaje_error)

def devolver403(cs, webroot):
    error403 = "HTTP/1.1 403 Forbidden\r\n"
    error403 = error403 + "Date: "
    error403 = error403 + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') +"\r\n"
    error403 = error403 + "Server: web.kaorisite.org\r\n"
    error403 = error403 + "Connection: "
    error403 = error403 + "keep-alive\r\n"
    error403 = error403 + "Keep-Alive: timeout = " + str(KEEP_ALIVE_TIME) + "\r\n"
    error403 = error403 + "Content-Length: "
    url = webroot + "/Error403.html"
    tamanoerror = os.stat(url).st_size
    ext = "html"
    error403 = error403 + str(tamanoerror) + "\r\n"
    error403 = error403 + "Content-Type: "
    error403 = error403 + filetypes[ext] + "\r\n\r\n"
    
    f = open(url, 'rb', BUFSIZE)
    texto = f.read(tamanoerror)
    encoded_error = error403.encode()
    mensaje_error = encoded_error + texto
    f.close()

    enviar_mensaje(cs, mensaje_error)

def devolver404(cs, webroot):
    error404 = "HTTP/1.1 404 Not found\r\n"
    error404 = error404 + "Date: "
    error404 = error404 + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') +"\r\n"
    error404 = error404 + "Server: web.kaorisite.org\r\n"
    error404 = error404 + "Connection: "
    error404 = error404 + "keep-alive\r\n"
    error404 = error404 + "Keep-Alive: timeout = " + str(KEEP_ALIVE_TIME) + "\r\n"
    error404 = error404 + "Content-Length: "
    url = webroot + "/Error404.html"
    tamanoerror = os.stat(url).st_size
    ext = "html"
    error404 = error404 + str(tamanoerror) + "\r\n"
    error404 = error404 + "Content-Type: "
    error404 = error404 + filetypes[ext] + "\r\n\r\n"
    
    f = open(url, 'rb', BUFSIZE)
    texto = f.read(tamanoerror)
    encoded_error = error404.encode()
    mensaje_error = encoded_error + texto
    f.close()

    enviar_mensaje(cs, mensaje_error)

def devolver405(cs, webroot):
    error405 = "HTTP/1.1 405 Not allowed\r\n"
    error405 = error405 + "Date: "
    error405 = error405 + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') +"\r\n"
    error405 = error405 + "Server: web.kaorisite.org\r\n"
    error405 = error405 + "Connection: "
    error405 = error405 + "keep-alive\r\n"
    error405 = error405 + "Keep-Alive: timeout = " + str(KEEP_ALIVE_TIME) + "\r\n"
    error405 = error405 + "Content-Length: "
    url = webroot + "/Error405.html"
    tamanoerror = os.stat(url).st_size
    ext = "html"
    error405 = error405 + str(tamanoerror) + "\r\n"
    error405 = error405 + "Content-Type: "
    error405 = error405 + filetypes[ext] + "\r\n\r\n"
    
    f = open(url, 'rb', BUFSIZE)
    texto = f.read(tamanoerror)
    encoded_error = error405.encode()
    mensaje_error = encoded_error + texto
    f.close()

    enviar_mensaje(cs, mensaje_error)

def devolver505(cs, webroot):
    error505 = "HTTP/1.1 505 Version Not Supported\r\n"
    error505 = error505 + "Date: "
    error505 = error505 + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') +"\r\n"
    error505 = error505 + "Server: web.kaorisite.org\r\n"
    error505 = error505 + "Connection: "
    error505 = error505 + "keep-alive\r\n"
    error505 = error505 + "Keep-Alive: timeout = " + str(KEEP_ALIVE_TIME) + "\r\n"
    error505 = error505 + "Content-Length: "
    url = webroot + "/Error505.html"
    tamanoerror = os.stat(url).st_size
    ext = "html"
    error505 = error505 + str(tamanoerror) + "\r\n"
    error505 = error505 + "Content-Type: "
    error505 = error505 + filetypes[ext] + "\r\n\r\n"
    
    f = open(url, 'rb', BUFSIZE)
    texto = f.read(tamanoerror)
    encoded_error = error505.encode()
    mensaje_error = encoded_error + texto
    f.close()

    enviar_mensaje(cs, mensaje_error)

def process_web_request(cs, webroot):
    """ Procesamiento principal de los mensajes recibidos.
        Típicamente se seguirá un procedimiento similar al siguiente (aunque el alumno puede modificarlo si lo desea)

        * Bucle para esperar hasta que lleguen datos en la red a través del socket cs con select()

            * Se comprueba si hay que cerrar la conexión por exceder TIMEOUT_CONNECTION segundos
              sin recibir ningún mensaje o hay datos. Se utiliza select.select

            * Si no es por timeout y hay datos en el socket cs.
                * Leer los datos con recv.
                * Analizar que la línea de solicitud y comprobar está bien formateada según HTTP 1.1
                    * Devuelve una lista con los atributos de las cabeceras.
                    * Comprobar si la versión de HTTP es 1.1
                    * Comprobar si es un método GET. Si no devolver un error Error 405 "Method Not Allowed".
                    * Leer URL y eliminar parámetros si los hubiera
                    * Comprobar si el recurso solicitado es /, En ese caso el recurso es index.html
                    * Construir la ruta absoluta del recurso (webroot + recurso solicitado)
                    * Comprobar que el recurso (fichero) existe, si no devolver Error 404 "Not found"
                    * Analizar las cabeceras. Imprimir cada cabecera y su valor. Si la cabecera es Cookie comprobar
                      el valor de cookie_counter para ver si ha llegado a MAX_ACCESOS.
                      Si se ha llegado a MAX_ACCESOS devolver un Error "403 Forbidden"
                    * Obtener el tamaño del recurso en bytes.
                    * Extraer extensión para obtener el tipo de archivo. Necesario para la cabecera Content-Type
                    * Preparar respuesta con código 200. Construir una respuesta que incluya: la línea de respuesta y
                      las cabeceras Date, Server, Connection, Set-Cookie (para la cookie cookie_counter),
                      Content-Length y Content-Type.
                    * Leer y enviar el contenido del fichero a retornar en el cuerpo de la respuesta.
                    * Se abre el fichero en modo lectura y modo binario
                        * Se lee el fichero en bloques de BUFSIZE bytes (8KB)
                        * Cuando ya no hay más información para leer, se corta el bucle

            * Si es por timeout, se cierra el socket tras el período de persistencia.
                * NOTA: Si hay algún error, enviar una respuesta de error con una pequeña página HTML que informe del error.
    """
    rlist = [cs]
    xlist = [cs]



    while (True):
        rsublist = []
        wsublist = []
        xlist = []
        (rsublist, wsublist, xsublist) = select.select(rlist, [], xlist, TIMEOUT_CONNECTION)
        if rsublist == [] and wsublist == [] and xsublist == []:
            cerrar_conexion(cs)
            break
        if rsublist == [cs]:
            datos = recibir_mensaje(cs)
            lineas = datos.split("\r\n")
            lineaSolicitud = lineas[0]
            match_solicitud = er_solicitud.fullmatch(lineaSolicitud)
            if (match_solicitud):
                version = match_solicitud.group(3)
                if (version != "1.1"):
                    return devolver505(cs, webroot)
                if not (lineaSolicitud.startswith("GET")):
                    return devolver405(cs, webroot)
                url = match_solicitud.group(2)
                (cadena1, separador, cadena2) = url.partition("?")
                if (cadena1 == "/"):
                    cadena1 = cadena1 + "index.html"
                cadena1 = webroot + cadena1
                if (not os.path.isfile(cadena1)):
                    return devolver404(cs, webroot)
                counter = process_cookies(lineas)
                if (counter == MAX_ACCESOS):
                    return devolver403(cs, webroot)
                tamano = os.stat(cadena1).st_size
                ext = os.path.basename(cadena1).split(".")[1]

                respuesta = ""
                respuesta = respuesta + "HTTP/1.1 "+CODIGO_RESPUESTA+" OK\r\n"
                respuesta = respuesta + "Date: "
                respuesta = respuesta + datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT') +"\r\n"
                respuesta = respuesta + "Server: web.kaorisite29.org\r\n"
                respuesta = respuesta + "Connection: "
                respuesta = respuesta + "keep-alive\r\n"
                respuesta = respuesta + "Keep-Alive: timeout = " + str(KEEP_ALIVE_TIME) + "\r\n"
                respuesta = respuesta + "Set-Cookie: cookie_counter="
                respuesta = respuesta + str(counter) + "; "
                respuesta = respuesta + "Max-Age=" + MAX_AGE + "\r\n"
                respuesta = respuesta + "Content-Length: "
                respuesta = respuesta + str(tamano) + "\r\n"
                respuesta = respuesta + "Content-Type: "
                respuesta = respuesta + filetypes[ext] + "\r\n\r\n"

                logger.info(cadena1)
                f = open(cadena1, 'rb', BUFSIZE)
                texto = f.read(tamano)
                encoded_resp = respuesta.encode()
                mensaje = encoded_resp + texto
                f.close()

                enviar_mensaje(cs, mensaje)
            else:
                return devolver400(cs, webroot)
        else:
            break

def main():
    """ Función principal del servidor
    """
    try:

        # Argument parser para obtener la ip y puerto de los parámetros de ejecución del programa. IP por defecto 0.0.0.0
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--port", help="Puerto del servidor", type=int, required=True)
        parser.add_argument("-ip", "--host", help="Dirección IP del servidor o localhost", required=True)
        parser.add_argument("-wb", "--webroot", help="Directorio base desde donde se sirven los ficheros (p.ej. /home/user/mi_web)")
        parser.add_argument('--verbose', '-v', action='store_true', help='Incluir mensajes de depuración en la salida')
        args = parser.parse_args()


        if args.verbose:
            logger.setLevel(logging.DEBUG)

        logger.info('Enabling server in address {} and port {}.'.format(args.host, args.port))

        logger.info("Serving files from {}".format(args.webroot))

        """ Funcionalidad a realizar
        * Crea un socket TCP (SOCK_STREAM)
        * Permite reusar la misma dirección previamente vinculada a otro proceso. Debe ir antes de sock.bind
        * Vinculamos el socket a una IP y puerto elegidos

        * Escucha conexiones entrantes

        * Bucle infinito para mantener el servidor activo indefinidamente
            - Aceptamos la conexión

            - Creamos un proceso hijo

            - Si es el proceso hijo se cierra el socket del padre y procesar la petición con process_web_request()

            - Si es el proceso padre cerrar el socket que gestiona el hijo.
        """
        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host, args.port))
        s.listen()

        while (True):
            (conn, addr) = s.accept()
            pid = os.fork()

            if (pid == 0):
                cerrar_conexion(s)
                process_web_request(conn, args.webroot)
                break

            else:
                cerrar_conexion(conn)
    except KeyboardInterrupt:
        True

if __name__== "__main__":
    main()