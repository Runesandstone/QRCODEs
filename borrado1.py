from PIL import Image
import qrcode
import os 

configuracion_qr = dict(
    version=4,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

qr_rojo = qrcode.QRCode(**configuracion_qr)
qr_verde = qrcode.QRCode(**configuracion_qr)
qr_azul = qrcode.QRCode(**configuracion_qr)



qr_rojo.add_data("https://github.com/lincolnloop/python-qrcode")
qr_azul.add_data("https://pillow.readthedocs.io/en/stable/handbook/tutorial.html")
qr_verde.add_data("https://music.youtube.com/")

qr_rojo.make(fit=True)
qr_verde.make(fit=True)
qr_azul.make(fit=True)


imgRed = qr_rojo.make_image(fill_color="black", back_color="white").convert("L")
imgGreen = qr_verde.make_image(fill_color="black", back_color="white").convert("L")
imgBlue = qr_azul.make_image(fill_color="black", back_color="white").convert("L")


qr_multiplexado = Image.merge("RGB", (imgRed, imgGreen, imgBlue))

qr_multiplexado.save("C:/Users/Usuario/Documents/Learning/qr_multiplexado.png")

print("Tu imagen se guardó en esta carpeta:", os.getcwd())


qr_escaneado = Image.open("C:/Users/Usuario/Documents/Learning/qr_multiplexado.png")

capa_roja, capa_verde, capa_azul = qr_escaneado.split()

#el qr "escaneado" se guardará en la carpeta actual del proyecto a menos que se especifique otra ruta de la siguiente manera:
capa_azul.save("C:/Users/Usuario/Documents/Learning/qr_azul.png")
capa_verde.save("C:/Users/Usuario/Documents/Learning/qr_verde.png")
capa_roja.save("C:/Users/Usuario/Documents/Learning/qr_rojo.png")