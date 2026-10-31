import math
import os
import sys
import zlib
import bson
import cv2
from PIL import Image
import qrcode
import zxingcpp


def empaquetar_archivo(ruta_archivo):
    
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
    print(f"Archivo empaquetado en BSON y comprimido con zlib. Tamaño final: {len(bytes_comprimidos)} bytes")
    return bytes_comprimidos

def dividir_bytes(bytes_datos):
    tamano_tercio = math.ceil(len(bytes_datos) / 3)
    bloque_r = bytes_datos[0:tamano_tercio]
    bloque_g = bytes_datos[tamano_tercio:tamano_tercio * 2]
    bloque_b = bytes_datos[tamano_tercio * 2:]
    print("tamaño_tercio:", tamano_tercio)
    
    print(f"Total de bytes comprimidos: {len(bytes_datos)}")
    print(f"  -> Capa Roja:  {len(bloque_r)} bytes")
    print(f"  -> Capa Verde: {len(bloque_g)} bytes")
    print(f"  -> Capa Azul:  {len(bloque_b)} bytes")
    
    return bloque_r, bloque_g, bloque_b

def generar_qr(ruta_entrada, ruta_qr_salida, error_correction=None):
    try:
        bytes_comprimidos = empaquetar_archivo(ruta_entrada)
        bloque_r, bloque_g, bloque_b = dividir_bytes(bytes_comprimidos)

        if error_correction is None:
            print("¿Qué corrección de errores deseas? Cuanto menor sea el porcentaje," \
            "menos datos pueden guardarse pero más datos se podrán recuperar en caso de daño")
            print("1. L (7%)\n2. M (15%)\n3. Q (25%)\n4. H (30%)")
            choose = int(input("Ingresa el número de la opción deseada (1-4): "))

            match choose:
                case 1:
                    error_correction = qrcode.constants.ERROR_CORRECT_L
                case 2:
                    error_correction = qrcode.constants.ERROR_CORRECT_M
                case 3:
                    error_correction = qrcode.constants.ERROR_CORRECT_Q
                case 4:
                    error_correction = qrcode.constants.ERROR_CORRECT_H
                case _:
                    print("Opción inválida. Se usará la corrección de errores por defecto (M).")
                    error_correction = qrcode.constants.ERROR_CORRECT_M


        configuracion_qr = dict(
            version=None,
            error_correction = error_correction,
            box_size=4,
            border=4,
        )   
        print(f"Configuración QR: {configuracion_qr}")
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
        raise

def escanear_qr(ruta_qr_salida):
    qr_escaneado = Image.open(ruta_qr_salida)
    capa_roja, capa_verde, capa_azul = qr_escaneado.split()
    capa_roja.save("lib/qr_erojo.png")
    capa_verde.save("lib/qr_everde.png")
    capa_azul.save("lib/qr_eazul.png")

    # AGREGADO: limitar ZXing a QR y conservar sus bytes sin convertirlos a texto.
    datos_rojos = zxingcpp.read_barcodes(
        capa_roja, formats=zxingcpp.BarcodeFormat.QRCode
    )
    datos_verdes = zxingcpp.read_barcodes(
        capa_verde, formats=zxingcpp.BarcodeFormat.QRCode
    )
    datos_azules = zxingcpp.read_barcodes(
        capa_azul, formats=zxingcpp.BarcodeFormat.QRCode
    )

    bytes_r = max((dato.bytes for dato in datos_rojos), key=len, default=b"")
    bytes_g = max((dato.bytes for dato in datos_verdes), key=len, default=b"")
    bytes_b = max((dato.bytes for dato in datos_azules), key=len, default=b"")


    print(f"Cabecera zlib recuperada: {bytes_r[:2]}")  

    print(f"Largo Capa Roja:  {len(bytes_r)}")
    print(f"Largo Capa Verde: {len(bytes_g)}")
    print(f"Largo Capa Azul:  {len(bytes_b)}")


    bytes_totales = bytes_r + bytes_g + bytes_b
    return bytes_totales

def reconstruir_archivo(bytes_totales):

    if bytes_totales:
        payload_bson_recuperado = zlib.decompress(bytes_totales)
        datos_recuperados = bson.decode(payload_bson_recuperado)

        nombre_orig = datos_recuperados["name"]
        ext_orig = datos_recuperados["ext"]
        contenido_binario = datos_recuperados["data"]

        directorio_salida = "lib/"
        ruta_salida_reconstruido = os.path.join(directorio_salida, f"{nombre_orig}_recuperado.{ext_orig}")

        with open(ruta_salida_reconstruido, "wb") as archivo_final:
            archivo_final.write(contenido_binario)

        print(f"Archivo recuperado: '{nombre_orig}_recuperado.{ext_orig}'")
        return ruta_salida_reconstruido

    raise ValueError("No se recuperaron bytes del QR; no es posible reconstruir el archivo.")
