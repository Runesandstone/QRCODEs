import base64
import os
import webview
import qrcode
from webview import FileDialog
from ZXING import generar_qr
from ZXING import escanear_qr
from ZXING import reconstruir_archivo
class BackendAPI:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def seleccionar_y_procesar(self):
        """Abre un diálogo nativo del S.O. para elegir un archivo y simula el proceso."""
        # Diálogo nativo para seleccionar archivo
        file_types = ('Archivos recomendados (*.csv;*.txt;*.json)', 'Todos los archivos (*.*)')
        result = self._window.create_file_dialog(FileDialog.OPEN, allow_multiple=False, file_types=file_types)
        
        if result:
            ruta_archivo = result[0]
            tamano = os.path.getsize(ruta_archivo)
            
            ruta_qr_salida = os.path.splitext(ruta_archivo)[0] + '_qr.png'
            
            generar_qr(
                ruta_archivo,
                ruta_qr_salida,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
            )
            with open(ruta_qr_salida, "rb") as archivo:
                imagen_qr = base64.b64encode(archivo.read()).decode("ascii")

            return {
                "status": "ok",
                "mensaje": f"Archivo cargado: {os.path.basename(ruta_archivo)}",
                "detalles": f"Tamaño: {tamano} bytes",
                "imagen": f"data:image/png;base64,{imagen_qr}",
            }
        
        return {"status": "cancel", "mensaje": "Selección cancelada."}

    def recuperar_archivo(self):
        file_types = ('Archivos QR (*.png;*.jpg;*.jpeg)',)
        result = self._window.create_file_dialog(FileDialog.OPEN, allow_multiple=False, file_types=file_types)
        
        if result:
            ruta_qr = result[0]

            bytes_totales = escanear_qr(ruta_qr)
            ruta_recuperada = reconstruir_archivo(bytes_totales)

            return {
                "status": "ok",
                "mensaje": f"Archivo QR cargado: {os.path.basename(ruta_qr)}",
                "detalles": f"Archivo recuperado en: {ruta_recuperada}",
            }
        
        return {"status": "cancel", "mensaje": "Selección cancelada."}

if __name__ == '__main__':
    api = BackendAPI()
    
    # Creamos la ventana nativa renderizando el HTML/CSS
    window = webview.create_window(
        title='Generador QRGB - Tester GUI',
        url=r'C:\Users\Usuario\Documents\Learning\QRCODEs\index.html',
        js_api=api,
        width=1000,
        height=1000,
        resizable=False
    )
    
    api.set_window(window)
    webview.start()