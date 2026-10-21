# TryHackMe MADNESS ROOM |  SPANISH ES
## by tunlp

![Room Logo](./screenshots/000_room_logo.png)

Para empezar, realizo un escaneo de puertos con `nmap`

![Nmap output](./screenshots/01_nmap_output.png)

Como existe un servicio `http` en el puerto `80`, ingreso la IP de la máquina en el navegador

![Web App](./screenshots/02_Web_Application.png)

Veo que es la página 'default' de `apache`, entretanto existe una imagen que no aparece, intento abrirla en el navegador

![Image Unavailable](./screenshots/03_unavailable_image.png)

Realizo `wget` para descargar la imagen completa

![Download Image](./screenshots/04_Download_Image.png)

Analizo la imagen con el comando `file` y responde con `thm.jpg: data`. El fichero es data, no contenido... De todas formas realizo un análisis con `binwalk` para ver si oculta archivos

![File Type](./screenshots/05_Hidden_Files.png)

Intento extraer los archivos ocultos con `foremost` y `7z`, pero ninguno funciona, por lo tanto procedo a analizar en `hexedit` para ver si su formato hexadecimal nos da alguna pista

![Hexadump](./screenshots/06_hexdump_1.png)

Los primeros 8 bytes del `hexdump` de la imagen dicen que el formato es `png` aunque se llame `thm.jpg`. Investigo sobre la cabecera y aprendo que los formatos `PNG` y `JPG/JPEG` tienen los 8 primeros bytes en el siguiente formato hexadecimal

```
PNG=>  89 50 4E 47 0D 0A 1A 0A
JPEG=> FF D8 FF E0 00 10 1A 4A 
```
Los siguientes 3 bytes en una imagen JPEG corresponden al formato. El último byte `4A` representa la letra `J`; a partir de él los siguientes 3 bytes deben formar la palabra `JFIF` | `46 49 46` (JPEG File Interchange Format), como una marca registrada que confirma que el archivo es `JPEG`, por lo tanto sustituiré los 11 primeros bytes actuales por los que corresponden a una imagen JPEG. 

![Sustitución Hexadecimal](./screenshots/07_Hex_Change.png)

Al guardar los cambios y abrir la imagen nuevamente, veo que ahora está disponible y revela el directorio oculto

![Hidden Directory](./screenshots/08_Fixed_Image.png)

Ingreso el directorio oculto en el navegador y encuentro un mensaje:

![Hidden Directory Message](./screenshots/09_Hidden_Directory_Web.png)

Pide que ingrese el número secreto, entretanto no hay una entrada para introducirlo. Inspecciono el código fuente de la página en busca de pistas...

![Page Source](./screenshots/10_Page_Source.png)

Dice que es un número entre 1 y 99, pero antes de realizar un bruteforce, necesito entender cómo hago que la página reconozca una entrada numérica... Después de un tiempo dando vueltas, intentando parámetros como `hiddenfoldername/?number=1`, veo que la web reconoce si utilizo `?secret=1`

![Valid Parameter](./screenshots/11_page_parameter.png)

Encontrada la forma de ingresar el número, creo un sencillo script en Python con la librería `requests` para intentar las 100 posibilidades. Como la web utiliza la palabra `wrong`, el opuesto es `right`, así que utilizo esta condición para encontrar el valor correcto sin tanta verbosidad del programa.

```py
import requests

for number in range(0,100):
    URL = f"http://<IP>/hiddendirectoryname/?secret={number}"
    response = requests.get(URL)
    if "right" in response.text:
        print(f"Correct number: {number}")
        print(response.text)
    else:
        pass

```

![Bruteforce Result](./screenshots/12_Correct_Number.png)

Con el número correcto, devuelve una combinación que aparenta ser una contraseña. Recuerdo que binwalk mostró en la imagen corrupta la presencia de firmas incrustradas, por lo tanto pruebo a extraer el contenido con `steghide` y me pide una contraseña. Ingreso la cadena encontrada anteriormente al acertar el número en la web y extrae un archivo de texto.

* La contraseña proporcionada contiene símbolos; para poder extraerla con `steghide` debes utilizar la flag `-p` y la contraseña dentro de '' para que no genere conflicto.

![Hidden Files](./screenshots/13_Extracted_text_1.png)

Al leer el fichero extraído, se revela un usuario con una combinación alfabética de caracteres.

![Username Found](./screenshots/14_Cat_Hidden.png)

Lo primero que intento es pasar la cadena alfabética por `Cyberchef` para ver si está en formato `base64` o algún otro... Después de muchas vueltas, intenté rotar los caracteres porque, ya que eran apenas letras, quizás con un desplazamiento `Caesar` podría encontrar una palabra que tenga más sentido para un usuario. Cyberchef proporciona `ROT13` como base, lo que significa un desplazamiento de 13 caracteres, aunque permite elegir cuántos desplazamientos quieres realizar. Sorprendentemente no fue necesario rotar desde el principio (1 posición, 2 posiciones, 3 p...) porque una palabra con mucho sentido apareció con los 13 desplazamientos base que proporciona el filtro.

![ROT13](./screenshots/15_ROT_13.png)

Por ahora tengo un usuario y una contraseña (para extraer los archivos). Me quedo bloqueado un buen tiempo hasta 'pensar fuera de la caja' e intentar investigar la imagen de la sala de TryHackMe.

![Room Pic](./screenshots/16_Room_PIC.png)

Descargo la imagen con `wget` y `binwalk` también me muestra la presencia de archivos incrustados, así que directamente intento extraer con `steghide`. Pide una contraseña, intento la anterior y no funciona, intento sin contraseña y extrae exitosamente.

![Steghide fail](./screenshots/17_Extracted_2.png)

Al leer el fichero veo que revela una contraseña...

![ssh password](./screenshots/18_Password_Found.png)

Ya que tengo un usuario y una contraseña, creo que es momento de entrar por `SSH`. (El usuario está oculto para no revelar pasos anteriores)

![ssh login](./screenshots/19_ssh_login.png)

Con `ls` veo un archivo de texto que resulta ser la primera `FLAG`

![cat flag 1](./screenshots/20_user_flag.png)

Ahora toca la tan esperada escalada de privilegios; para ello busco binarios que contengan el `SUID` (ejecutables de administrador 'root' que pueden ser ejecutados por cualquier usuario)

![SUID](./screenshots/21_SUID_Binary.png)

De todos los binarios presentes en mi búsqueda, en particular `screen-4.5.0` me llama la atención, sobre todo por la presencia de `screen-4.5.0.old`, así que investigo más sobre este binario.
screen es una herramienta que permite mantener sesiones de terminal abiertas en segundo plano. La versión 4.5.0 tenía una vulnerabilidad que permitía ejecutar código con privilegios elevados en determinadas condiciones. Si screen pertenece a root y tiene SUID activado, el exploit puede llegar a ejecutar comandos como root.

![Exploit Found](./screenshots/22_exploit_found.png)

En la máquina víctima, creo un fichero `screen-4-5-0-exploit.sh` y, como tiene `vim`, reescribo el código, le doy los permisos y ejecuto.

![Use exploit](./screenshots/23_exploit_permit.png)

![I AM ROOT](./screenshots/24_IAM_ROOT.png)

Navego hasta el directorio `/root` y con `ls` veo la `FLAG` de `root` y la leo.

![Root FLag](./screenshots/25_root_flag.png)

## GRACIAS - By tunlp

![Pwned by tunlp](./screenshots/26_pwned_tunlp.png)
