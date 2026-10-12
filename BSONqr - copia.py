import math
import os
import sys
import zlib
import bson
import cv2
from PIL import Image
import qrcode
from pyzbar.pyzbar import decode
import pyzbar

print("ayudame2")
def empaquetar_archivo_a_bson(ruta_archivo):
    
    nombre_archivo = os.path.basename(ruta_archivo)
    nombre, extension = os.path.splitext(nombre_archivo)
    extension = extension.lstrip(".")  # Quita el punto inicial (ej: ".zip" -> "zip")

    with open(ruta_archivo, "rb") as f:
        bytes_archivo = f.read()

    # Estructura de datos BSON con metadatos + BinData nativo
    payload_bson = bson.encode({
        "name": nombre,
        "ext": extension,
        "size": len(bytes_archivo),
        "data": bytes_archivo
    })

    # Compresión binaria pura
    bytes_comprimidos = zlib.compress(payload_bson)
    return bytes_comprimidos


def dividir_bytes_en_3_capas(bytes_datos):
    tamano_tercio = math.ceil(len(bytes_datos) / 3)
    bloque_r = bytes_datos[0:tamano_tercio]
    bloque_g = bytes_datos[tamano_tercio:tamano_tercio * 2]
    bloque_b = bytes_datos[tamano_tercio * 2:]
    
    print(f"Total de bytes comprimidos: {len(bytes_datos)}")
    print(f"  -> Capa Roja:  {len(bloque_r)} bytes")
    print(f"  -> Capa Verde: {len(bloque_g)} bytes")
    print(f"  -> Capa Azul:  {len(bloque_b)} bytes")
    
    return bloque_r, bloque_g, bloque_b



# RUTA DEL ARCHIVO ENTRADA
ruta_entrada = "C:/Users/Usuario/Documents/Learning/QRCODEs/Elctronica.csv"
ruta_qr_salida = "C:/Users/Usuario/Documents/Learning/QRCODEs/qr_txt_multiplexado.png"

try:
    bytes_comprimidos = empaquetar_archivo_a_bson(ruta_entrada)
    bloque_r, bloque_g, bloque_b = dividir_bytes_en_3_capas(bytes_comprimidos)

    configuracion_qr = dict(
        version=40,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=4,
    )

    qr_rojo = qrcode.QRCode(**configuracion_qr)
    qr_verde = qrcode.QRCode(**configuracion_qr)
    qr_azul = qrcode.QRCode(**configuracion_qr)

    if bloque_r:
        qr_rojo.add_data(bloque_r, optimize=0)
    if bloque_g:
        qr_verde.add_data(bloque_g, optimize=0)
    if bloque_b:
        qr_azul.add_data(bloque_b, optimize=0)



    qr_rojo.make(fit=True)
    qr_verde.make(fit=True)
    qr_azul.make(fit=True)

    imgRed = qr_rojo.make_image(fill_color="black", back_color="white").convert("L")
    imgGreen = qr_verde.make_image(fill_color="black", back_color="white").convert("L")
    imgBlue = qr_azul.make_image(fill_color="black", back_color="white").convert("L")

    qr_multiplexado = Image.merge("RGB", (imgRed, imgGreen, imgBlue))
    qr_multiplexado.save(ruta_qr_salida)
    print(f"¡Éxito! Tu QR multiplexado se guardó en: {ruta_qr_salida}\n")

except Exception as e:
    print(f"Ocurrió un error en la generación: {e}")


qr_escaneado = Image.open(ruta_qr_salida)

capa_roja, capa_verde, capa_azul = qr_escaneado.split()

capa_roja.save("C:/Users/Usuario/Documents/Learning/QRCODEs/qr_erojo.png")
capa_verde.save("C:/Users/Usuario/Documents/Learning/QRCODEs/qr_everde.png")
capa_azul.save("C:/Users/Usuario/Documents/Learning/QRCODEs/qr_eazul.png")
# 1. Escaneo con el parche
datos_rojos = decode(capa_roja, binary=True)
datos_verdes = decode(capa_verde, binary=True)
datos_azules = decode(capa_azul, binary=True)

bytes_r = max([d.data for d in datos_rojos], key=len) if datos_rojos else b""
bytes_g = max([d.data for d in datos_verdes], key=len) if datos_verdes else b""
bytes_b = max([d.data for d in datos_azules], key=len) if datos_azules else b""

# 2. FUNCIÓN MÁGICA: Revertimos la conversión UTF-8 de ZBar a Latin-1 puro
def des_transcodificar_zbar(datos_corruptos):
    try:
        return datos_corruptos.decode('utf-8').encode('iso-8859-1')
    except Exception:
        return datos_corruptos

bytes_r = des_transcodificar_zbar(bytes_r)
bytes_g = des_transcodificar_zbar(bytes_g)
bytes_b = des_transcodificar_zbar(bytes_b)

# 3. Recorte exacto (ahora que los bytes volvieron a su tamaño real)
tamano_tercio = 470
bytes_r = bytes_r[:tamano_tercio]
bytes_g = bytes_g[:tamano_tercio]
bytes_b = bytes_b[:468]

print(f"Cabecera zlib recuperada: {bytes_r[:2]}")  # ¡Ahora sí dirá b'x\x9c'!

bytes_totales = bytes_r + bytes_g + bytes_b

if bytes_totales:
    try:
        payload_bson_recuperado = zlib.decompress(bytes_totales)
        datos_recuperados = bson.decode(payload_bson_recuperado)

        nombre_orig = datos_recuperados["name"]
        ext_orig = datos_recuperados["ext"]
        contenido_binario = datos_recuperados["data"]

        directorio_salida = "C:/Users/Usuario/Documents/Learning/QRCODEs"
        ruta_salida_reconstruido = os.path.join(directorio_salida, f"{nombre_orig}_recuperado.{ext_orig}")

        with open(ruta_salida_reconstruido, "wb") as archivo_final:
            archivo_final.write(contenido_binario)

        print("\n==========================================")
        print("¡SISTEMA VALIDADO CON ÉXITO!")
        print(f"Archivo resucitado: '{nombre_orig}_recuperado.{ext_orig}'")
        print("==========================================")

    except Exception as e:
        print(f"Error al descompilar el paquete BSON/zlib: {e}")