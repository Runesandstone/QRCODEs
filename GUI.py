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
            
            try:
                rutas_qr = generar_qr(
                    ruta_archivo,
                    ruta_qr_salida,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                )
            except Exception as e:
                return {"status": "error", "mensaje": f"Error al generar el QR: {e}"}

            imagenes = []
            for ruta in rutas_qr:
                with open(ruta, "rb") as archivo:
                    b64 = base64.b64encode(archivo.read()).decode("ascii")
                imagenes.append(f"data:image/png;base64,{b64}")

            return {
                "status": "ok",
                "mensaje": f"Archivo cargado: {os.path.basename(ruta_archivo)}",
                "detalles": f"Tamaño: {tamano} bytes. Imágenes generadas: {len(rutas_qr)}",
                "imagenes": imagenes,
            }
        
        return {"status": "cancel", "mensaje": "Selección cancelada."}

    def recuperar_archivo(self):
        file_types = ('Archivos QR (*.png;*.jpg;*.jpeg)',)
        result = self._window.create_file_dialog(FileDialog.OPEN, allow_multiple=True, file_types=file_types)
        
        if result:
            rutas_qr = list(result)

            try:
                bytes_totales = escanear_qr(rutas_qr)
                ruta_recuperada = reconstruir_archivo(bytes_totales)
            except Exception as e:
                return {"status": "error", "mensaje": f"No se pudo recuperar: {e}"}

            nombres = ", ".join(os.path.basename(r) for r in rutas_qr)
            return {
                "status": "ok",
                "mensaje": f"QR cargado(s): {nombres}",
                "detalles": f"Archivo recuperado en: {ruta_recuperada}",
            }
        
        return {"status": "cancel", "mensaje": "Selección cancelada."}

if __name__ == '__main__':
    api = BackendAPI()
    
    # Creamos la ventana nativa renderizando el HTML/CSS
    window = webview.create_window(
        title='Generador QRGB - Tester GUI',
        url=os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"),
        js_api=api,
        width=1000,
        height=1000,
        resizable=False
    )
    
    api.set_window(window)
    webview.start()