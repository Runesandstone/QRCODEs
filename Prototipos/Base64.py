import base64
import math
import os
import qrcode
import qrcode.constants
from PIL import Image
from pyzbar.pyzbar import decode
import cv2
import bson
import zlib
import sys


def preparar_archivo_para_qr(bytes_datos, tamano_bloque=2953):
    texto_base64 = base64.b64encode(bytes_datos).decode("utf-8")
    print(f"Cadena Base64 de BSON generada: {len(texto_base64)} caracteres")

    bloques = []
    for i in range(0, len(texto_base64), tamano_bloque):
        bloques.append(texto_base64[i : i + tamano_bloque])

    print(f"Total de bloques generados: {len(bloques)}")
    for idx, b in enumerate(bloques):
        print(f"  -> Bloque {idx}: {len(b)} caracteres")

    return bloques


# TODO: PONER LA RUTA DEL ARCHIVO AQUI
ruta_excel = r"C:\Users\Usuario\Documents\Learning\proyecto_biblioteca.zip"


def empaquetar_archivo_a_bson(ruta_archivo):
    # Separar correctamente el nombre del archivo y la extensión
    nombre_archivo = os.path.basename(ruta_archivo)
    nombre, extension = os.path.splitext(nombre_archivo)
    extension = extension.lstrip(".")  # Quita el punto inicial (ej: ".zip" -> "zip")

    with open(ruta_archivo, "rb") as f:
        bytes_archivo = f.read()

    payload_bson = bson.encode({
        "name": nombre,
        "ext": extension,
        "size": len(bytes_archivo),
        "data": bytes_archivo
    })

    bytes_comprimidos = zlib.compress(payload_bson)
    return bytes_comprimidos



# Ejemplos de uso real:
bytes_excel = empaquetar_archivo_a_bson(ruta_excel)  # Empaquetar el archivo ZIP

def obtener_peso_variable(variable):
    """
    Retorna el tamaño en bytes que ocupa la variable en memoria.
    """
    try:
        return sys.getsizeof(variable)
    except Exception as e:
        print(f"Error al obtener el tamaño: {e}")
        return None
bytes_comprimidos = empaquetar_archivo_a_bson(ruta_excel)

try:
    mis_bloques = preparar_archivo_para_qr(ruta_excel, tamano_bloque=2953)

    configuracion_qr = dict(
        version=40,  #
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,  
        border=4,
    )

    qr_rojo = qrcode.QRCode(**configuracion_qr)
    qr_verde = qrcode.QRCode(**configuracion_qr)
    qr_azul = qrcode.QRCode(**configuracion_qr)

    if len(mis_bloques) >= 1:
        qr_rojo.add_data(mis_bloques[0])
    if len(mis_bloques) >= 2:
        qr_verde.add_data(mis_bloques[1])
    if len(mis_bloques) >= 3:
        qr_azul.add_data(mis_bloques[2])

    qr_rojo.make(fit=True)
    qr_verde.make(fit=True)
    qr_azul.make(fit=True)

    imgRed = qr_rojo.make_image(
        fill_color="black", back_color="white"
    ).convert("L")
    imgGreen = qr_verde.make_image(
        fill_color="black", back_color="white"
    ).convert("L")
    imgBlue = qr_azul.make_image(
        fill_color="black", back_color="white"
    ).convert("L")

    qr_multiplexado = Image.merge("RGB", (imgRed, imgGreen, imgBlue))

    ruta_guardado = "C:/Users/Usuario/Documents/Learning/qr_excel_multiplexado.png"
    qr_multiplexado.save(ruta_guardado)
    print(f"¡Éxito! Tu QR con el Excel se guardó en: {ruta_guardado}")

except Exception as e:
    print(f"Ocurrió un error: {e}")


    

qr_escaneado = Image.open("C:/Users/Usuario/Documents/Learning/qr_excel_multiplexado.png")

capa_roja, capa_verde, capa_azul = qr_escaneado.split()

#el qr "escaneado" se guardará en la carpeta actual del proyecto a menos que se especifique otra ruta de la siguiente manera:
capa_azul.save("C:/Users/Usuario/Documents/Learning/qr_eazul.png")
capa_verde.save("C:/Users/Usuario/Documents/Learning/qr_everde.png")
capa_roja.save("C:/Users/Usuario/Documents/Learning/qr_erojo.png")


datos_azules = decode(capa_azul)

if datos_azules:
    # .data devuelve los bytes. Los decodificamos a texto (que será nuestro Base64)
    texto_base64_bloque3 = datos_azules[0].data.decode("utf-8")
    print("Bloque 3 extraído con éxito!")
else:
    print("No se pudo leer el QR de la capa roja")


datos_verdes = decode(capa_verde)

if datos_verdes:
    # .data devuelve los bytes. Los decodificamos a texto (que será nuestro Base64)
    texto_base64_bloque2 = datos_verdes[0].data.decode("utf-8")
    print("Bloque 2 extraído con éxito!")
else:
    print("No se pudo leer el QR de la capa verde")


datos_rojos = decode(capa_roja)

if datos_rojos:
    # .data devuelve los bytes. Los decodificamos a texto (que será nuestro Base64)
    texto_base64_bloque1 = datos_rojos[0].data.decode("utf-8")
    print("Bloque 1 extraído con éxito!")
else:
    print("No se pudo leer el QR de la capa roja")

texto_base64_completo = texto_base64_bloque1 + texto_base64_bloque2 + texto_base64_bloque3
# TODO: PONER LA RUTA DEL ARCHIVO RECONSTRUIDO AQUÍ
ruta_salida_reconstruido = "C:/Users/Usuario/Documents/Learning/SQL.zip"
if texto_base64_completo:
    try:
        # Traducir la cadena Base64 gigante de vuelta a bytes binarios originales
        bytes_archivo_reconstruido = base64.b64decode(texto_base64_completo)
        
        # Escribir los bytes en un nuevo archivo ('wb' = write binary)gggg
        with open(ruta_salida_reconstruido, "wb") as archivo_final:
            archivo_final.write(bytes_archivo_reconstruido)
            
        print(f"\n¡SISTEMA VALIDADO CON ÉXITO!")
        print(f"Tu archivo original ha sido resucitado en: {ruta_salida_reconstruido}")
        
    except Exception as e:
        print(f"Error al decodificar el Base64 o escribir el archivo: {e}")
else:
    print("Error: No se recuperaron datos de ninguna capa para armar el archivo.")