import math
import os
import zlib
import bson
from PIL import Image
import qrcode
from qrcode import util
import zxingcpp

V_MAX = 20          
HEADER_SIZE = 4     # índice (1 B), total de imágenes (1 B), id de sesión (2 B)


def empaquetar_archivo(ruta_archivo):
    nombre_archivo = os.path.basename(ruta_archivo)
    nombre, extension = os.path.splitext(nombre_archivo)
    extension = extension.lstrip(".")

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


def capacidad_bytes(version, ec):
    bits = util.BIT_LIMIT_TABLE[ec][version]
    return (bits - 4 - util.length_in_bits(util.MODE_8BIT_BYTE, version)) // 8


def planificar(n_bytes, ec, v_max=V_MAX, cap_fn=capacidad_bytes):
    cap_max = cap_fn(v_max, ec) - HEADER_SIZE
    n_imagenes = max(1, math.ceil(math.ceil(n_bytes / cap_max) / 3))
    por_qr = math.ceil(n_bytes / (3 * n_imagenes))
    for v in range(1, v_max + 1):
        if cap_fn(v, ec) - HEADER_SIZE >= por_qr:
            return n_imagenes, v, por_qr
    raise RuntimeError("No hay versión que alcance")


def dividir_bytes(datos, n_imagenes, por_qr, sesion):
    bloques = []
    for i in range(n_imagenes):
        trio = []
        for c in range(3):
            ini = (i * 3 + c) * por_qr
            cab = bytes([i, n_imagenes]) + sesion.to_bytes(2, "big")
            trio.append(cab + datos[ini:ini + por_qr])
        bloques.append(tuple(trio))
    return bloques


def _rutas_salida(ruta, n):
    if n == 1:
        return [ruta]
    base, ext = os.path.splitext(ruta)
    return [f"{base}_{i+1}de{n}{ext}" for i in range(n)]


def _qr_gris(datos, version, ec):
    qr = qrcode.QRCode(version=version, error_correction=ec, box_size=4, border=4)
    qr.add_data(datos, optimize=0)
    qr.make(fit=False)  # versión fija: todos del mismo tamaño
    return qr.make_image(fill_color="black", back_color="white").convert("L")


def generar_qr(ruta_entrada, ruta_qr_salida, error_correction=None):
    try:
        bytes_comprimidos = empaquetar_archivo(ruta_entrada)

        if error_correction is None:
            print("¿Qué corrección de errores deseas? Cuanto menor sea el porcentaje, "
                  "más datos caben pero menos se pueden recuperar en caso de daño")
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
                    print("Opción inválida. Se usará la corrección por defecto (M).")
                    error_correction = qrcode.constants.ERROR_CORRECT_M

        n_img, version, por_qr = planificar(len(bytes_comprimidos), error_correction)
        print(f"Plan: {n_img} imagen(es), versión {version}, {por_qr} bytes por canal")

        rutas = _rutas_salida(ruta_qr_salida, n_img)
        sesion = int.from_bytes(os.urandom(2), "big")  # distingue este archivo de otros
        bloques = dividir_bytes(bytes_comprimidos, n_img, por_qr, sesion)
        for ruta, trio in zip(rutas, bloques):
            capas = [_qr_gris(b, version, error_correction) for b in trio]
            Image.merge("RGB", capas).save(ruta)
            print(f"¡Éxito! QR multiplexado guardado en: {ruta}")
        return rutas

    except Exception as e:
        print(f"Ocurrió un error en la generación: {e}")
        raise


def _leer_canal(capa):
    res = zxingcpp.read_barcodes(capa, formats=zxingcpp.BarcodeFormat.QRCode)
    return max((r.bytes for r in res), key=len, default=b"")


def escanear_qr(rutas):
    if isinstance(rutas, str):
        rutas = [rutas]
    if not rutas:
        raise ValueError("No se indicó ninguna imagen.")

    por_imagen = {}
    sesion = total = None
    problemas = []

    for ruta in rutas:
        nombre = os.path.basename(ruta)
        trio = tuple(_leer_canal(c) for c in Image.open(ruta).convert("RGB").split())

        ilegibles = [("RGB")[c] for c, b in enumerate(trio) if len(b) < HEADER_SIZE]
        if ilegibles:
            problemas.append(f"{nombre}: no se pudo leer el canal {', '.join(ilegibles)}")
            continue

        if len({b[:HEADER_SIZE] for b in trio}) != 1:
            problemas.append(f"{nombre}: los tres canales tienen cabeceras distintas")
            continue

        idx, t, ses = trio[0][0], trio[0][1], trio[0][2:HEADER_SIZE]
        if idx >= t:
            problemas.append(f"{nombre}: cabecera corrupta (imagen {idx + 1} de {t})")
            continue

        if sesion is None:
            sesion, total = ses, t          # la primera imagen válida fija el conjunto
        elif ses != sesion or t != total:
            problemas.append(f"{nombre}: pertenece a otro archivo")
            continue

        if idx in por_imagen:
            if por_imagen[idx] != trio:
                problemas.append(f"{nombre}: repite la imagen {idx + 1} con otro contenido")
            continue                         # repetida idéntica: se ignora
        por_imagen[idx] = trio

    if total is not None:
        faltan = [i + 1 for i in range(total) if i not in por_imagen]
        if faltan:
            problemas.append(f"Faltan las imágenes {faltan} de {total}")

    if problemas or total is None:
        raise ValueError("; ".join(problemas) or "No se pudo leer ninguna imagen.")

    return b"".join(b[HEADER_SIZE:] for i in range(total) for b in por_imagen[i])


def reconstruir_archivo(bytes_totales):
    if bytes_totales:
        payload_bson_recuperado = zlib.decompress(bytes_totales)
        datos_recuperados = bson.decode(payload_bson_recuperado)

        nombre_orig = datos_recuperados["name"]
        ext_orig = datos_recuperados["ext"]
        contenido_binario = datos_recuperados["data"]

        directorio_salida = "lib/"
        os.makedirs(directorio_salida, exist_ok=True)
        ruta_salida_reconstruido = os.path.join(directorio_salida, f"{nombre_orig}_recuperado.{ext_orig}")

        with open(ruta_salida_reconstruido, "wb") as archivo_final:
            archivo_final.write(contenido_binario)

        print(f"Archivo recuperado: '{nombre_orig}_recuperado.{ext_orig}'")
        return ruta_salida_reconstruido

    raise ValueError("No se recuperaron bytes del QR; no es posible reconstruir el archivo.")
