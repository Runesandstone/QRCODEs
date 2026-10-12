# Proyecto QR multiplexado

Este repositorio reúne varios prototipos para generar, separar y reconstruir información a través de códigos QR usando capas RGB.

## Objetivo

La idea central es aprovechar la separación de canales de una imagen RGB para ocultar o distribuir datos en tres QR distintos:

- capa roja
- capa verde
- capa azul

Luego, al combinar estas capas en una sola imagen, se obtiene un QR multiplexado que puede contener información más grande de la que cabría en un solo código.

## Archivos principales

### 1) `Prototipo1.py`

Es el primer prototipo funcional.

- genera 3 códigos QR con distintas URLs
- convierte cada QR a escala de grises
- combina las tres imágenes con `Image.merge("RGB", ...)`
- guarda la imagen resultante como `qr_multiplexado.png`
- separa la imagen en sus 3 canales y guarda cada capa por separado

Este archivo sirve como demostración del concepto de multiplexado por canales RGB.

### 2) `Base64.py`

Es una versión experimental donde se intenta codificar un archivo en Base64 para dividirlo en bloques y distribuir esos bloques entre tres QR.

Flujo:

1. leer un archivo
2. convertirlo a Base64
3. dividir la cadena en bloques
4. guardar cada bloque en una capa diferente
5. escanear las capas
6. recomponer la cadena Base64
7. decodificarla y reconstruir el archivo original

Es un prototipo útil para entender cómo fragmentar datos antes de codificarlos en QR.

### 3) `BSONqr.py`

Es la versión más avanzada y funcional del proyecto.

Incluye:

- empaquetado de un archivo a BSON
- compresión con `zlib`
- división del contenido en 3 bloques para distribuirlos en las capas RGB
- generación de tres QR con los datos en cada capa
- reconstrucción del archivo original a partir del escaneo de las capas
s
El proceso es:

1. obtener el archivo de entrada
2. extraer nombre y extensión
3. codificarlo como documento BSON con:
   - `name`
   - `ext`
   - `size`
   - `data`
4. comprimir el BSON con `zlib` 
5. dividir el payload comprimido en 3 partes
6. generar un QR por cada parte
7. fusionar las 3 capas en una imagen RGB
8. escanear la imagen y recuperar cada capa
9. reconstruir el archivo con `bson.decode()` y `zlib.decompress()`

Esto permite transmitir archivos binarios (CSV, ZIP, etc.) mediante códigos QR.

### 4) `BSONqr - ZXING.py`

Es una copia de prueba/backup del enfoque anterior. Deja de utilizar pyzbar para la generacion y lectura de los códigos QR y pasa a usar zxingcpp, que muestra un mejor desempeño en la lectura de los datos binarios, mismos que se corromían e imposibilitaban la lectura en pyzbar. 

Archivos probados, subidos y descomprimidos correctamente:
1. `markdown-example.md`, de 26.7KB (Aproximadamente, el máximo tamaño permitido para un markdown)
2. `tester.csv`, de 61.2 KB (Aproximadamente, el máximo tamaño permitido para un CSV) 
3. `GUI.java`, de 15 KB (Tamaño maximo no probado)
4. `Elctronica.csv`, de de 6 KB
5. `steve.jpg`, de 8.39KB (Tamaño aproximado máximo permitido para un JPG)
6. `documento.docx`, de 8.61 KB (Tamaño aproximado máximo permitido para un DOCX)

## Dependencias

Los scripts usan principalmente:

- `qrcode`
- `Pillow` (`PIL`)
- `pyzbar`
- `opencv-python` (`cv2`)
- `bson`
- `zlib`
- `zxingcpp`

## Flujo general del proyecto

```text
Archivo original
        |
        v
BSON + zlib
        |
        v
dividir en 3 bloques
        |
        v
3 QR (rojo, verde, azul)
        |
        v
imagen RGB multiplexada
        |
        v
escaneo de capas
        |
        v
reconstrucción del archivo
```

## Archivos relevantes

- [BSONqr.py](BSONqr.py)
- [Base64.py](Base64.py)
- [Prototipo1.py](Prototipo1.py)
- [BSONqr - copia.py](BSONqr%20-%20copia.py)

## Siguiente paso TODO

Plan para continuar con:

- automatización de la selección de la ruta del archivo
- validación de tamaño máximo por QR
- interfaz gráfica para generar y recuperar QR -- principalmente para idea visual del funcionamiento (no prioritario)
