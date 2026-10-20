# TryHack3M: Bricks Heist
### by  tunlp

![Room Logo](screenshots/00_Room_Logo.png)

Agrego a `/etc/hosts` la `IP` y `bricks.thm`.

![Website](screenshots/01_Web_app.png)

identifico que la aplicación web presenta un ícono de `Wordpress`, ya es una pista (...)

Realizo un escaneo `nmap -sV -p- -Pn <IP>`
![Nmap Scan](screenshots/02_nmap_report.png)

Nos presenta diversos servicios como `ssh:22`,`https:443`,`mysql:3306`,`OS:Ubuntu Linux`.Pero primero hay que pasar por `Wordpress`.Normalmente las aplicaciones Wordpress tienen `/wp-login.php` o `/wp-admin.php`.

![Wordpress Login](screenshots/03_Wp_Login.png)

Utilizo `Wpscan`, una herramienta que sirve para detectar vulnerabilidades en Wordpress.

![Wordpress Vulnerability](screenshots/04_CVE_Version.png)

Encuentro la versión vulnerable `1.9.5` de `Bricks`, un Software de construcción visual para Wordpress, la CVE me indica que la vulnerabilidad permite inyección de código. Busco la CVE y encuentro el exploit en github https://github.com/Chocapikk/CVE-2024-25600

Instalo los `requirements.txt` y ejecuto el exploit en `https://bricks.thm`, exitoso abre una shell dónde identifico que soy usuario `apache`.
![Shell Apache](screenshots/05_Shell_Apache.png)

Con un `ls` encuentro el `Hidden txt file in a web folder(FLAG)`:

![First Flag](screenshots/06_Flag_One.png)

Pregunta cual es el proceso sospechoso y sugiere utilizar `systemctl | grep "running`

![First Flag](screenshots/07_Suspicious_Process.png)

`ubuntu.service TRYHACK3M`, suficientemente sospechoso. Realizo `systemctl cat ubuntu.service`

![Cat Service](screenshots/08_Investigating_Service.png)

```sh
Restart=on-failure #persistencia(?)
WantedBy=multi-user.target #lateralización(?)
```
Arranca desde `/lib/NetworkManager/nm-inet-dialog`

![Cat Service](screenshots/09_Service_Prop.png)

El nombre del ejecutable `nm-inet-dialog` es la respuesta a la segunda pregunta, y `ubuntu.service` la respuesta de la tercera pregunta.
En resumen, el proceso nm-inet-dialog se hace pasar por ubuntu.service.

Con `ls -la /lib/NetworkManager/` investigo que más hay en el directorio
![Ls Folder](screenshots/11_ls_dir.png)

Como el binario sospechoso se llama `-inet-` , ví `inet.conf` y lo leí para ver si estaba relacionado.

![LogFileFound](screenshots/12_Miner_log.png)

Aparece la actividad maliciosa del `miner` y `inet.conf` es el nombre del archivo `log` de la instáncia del minador. También preguntan el `address` de la instáncia(...) desplazando veo el id:

![Miner ID](screenshots/13_Miner_ID.png)

`ID:5757314e65474e5962484a4f656d787457544e424e574648555446684d3070735930684b616c70555a7a566b52335276546b686b65575248647a525a57466f77546b64334d6b347a526d685a6255313459316873636b35366247315a4d304531595564476130355864486c6157454a3557544a564e453959556e4a685246497a5932355363303948526a4a6b52464a7a546d706b65466c525054303d`

Me fijo en los caracteres del ID e identifico numeros y letras que van de `a - f` ,probablemente esta en hexadecimal, por lo tanto lo analizo con `CyberChef`:

![CyberChef 1](screenshots/14_CyberCHef_1.png)

veo que el `output` me da un valor que termina en `=`, normalmente este final se asemeja a `base64`, lo paso por el filtro base64 y vuelvo a encontrarme un final con `==`, vuelvo a pasar por base64 e identifico una cadena que parece ser un address de Criptomonedas.

![Wallet ID](screenshots/15_Wallets.png)

Identifico un patrón `bc1` , parece que son dos wallets, investigo la primera `bc1qyk79fcp9hd5kreprce89tkh4wrtl8avt4l67qa`(Respuesta a la quinta pregunta) en `Metasleuth`
![Metasleuth](screenshots/16_Wallet_Analysis.png)

Veo que realiza transferencias a una wallet de `KuCoin`,que además esta `santioned`, por lo tanto podría contener más informacióm:

![KuCoin Wallet](screenshots/17_Hacking_Group.png)

Al buscar la wallet de KuCoin en `google` rapidamente encuentro un link del departamento del tesoro de EEUU que relaciona la dirección de wallet con el grupo de ransomware `LockBit` (Respuesta a la última pregunta)

![Pwned by tunlp](screenshots/18_Pwned_tunlp.png)
