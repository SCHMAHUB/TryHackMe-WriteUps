# TryHack3M: Bricks Heist ROOM
### by tunlp

![Room Logo](./screenshots/00_Room_Logo.png)



I add the `IP` and `bricks.thm` to `/etc/hosts`.


![Website](./screenshots/01_Web_app.png)

I notice that the web application shows a `Wordpress` icon, which is already a clue (...)

I run a port scan `nmap -sV -p- -Pn <IP>`

![Nmap Scan](./screenshots/02_nmap_report.png)

It shows several services such as `ssh:22`, `https:443`, `mysql:3306`, `OS:Ubuntu Linux`. But first we have to get through `Wordpress`. Wordpress applications usually have `/wp-login.php` or `/wp-admin.php`.

![Wordpress Login](./screenshots/03_Wp_Login.png)

I use `Wpscan`, a tool used to detect vulnerabilities in Wordpress.

![Wordpress Vulnerability](./screenshots/04_CVE_Version.png)

I find the vulnerable version `1.9.5` of `Bricks`, a visual site builder for Wordpress; the CVE tells me the vulnerability allows code injection. I look up the CVE and find the exploit on github https://github.com/Chocapikk/CVE-2024-25600

At the code level, the `Bricks\Query` class is used to render a `POST` query in WordPress, and it contains the following vulnerable method:

```php
public static function prepare_query_vars_from_settings( $settings = [], $fallback_element_id = '' )
{
    // FRAGMENT START
    
    $execute_user_code = function () use ( $php_query_raw ) {
        $user_result = null; // initializes a variable to capture the code

        // captures the output of the user's code using output buffering
        ob_start();
        //*CRITICAL*
        $user_result = eval( $php_query_raw ); // executes the user's code
        ob_get_clean(); // Get the captured output
        
        return $user_result; // returns the result of the user's code
    };
    
    // FRAGMENT END
}
```

The critical part happens with the `$user_result` variable, which receives the `$php_query_raw` passed to an `eval` function, and that function is dangerous... To learn more about how the vulnerability works, visit https://snicco.io/vulnerability-disclosure/bricks/unauthenticated-rce-in-bricks-1-9-6

![](./screenshots/UPDT_1_0XCriticalMethod.png)

I install the `requirements.txt` from the cloned repository and run the exploit against `https://bricks.thm`; on success, it opens a shell where I identify that I am the `apache` user.
![Shell Apache](./screenshots/05_Shell_Apache.png)

In short, the exploit succeeds because in the code the `process_response()` function validates against the `status_code` and `check_vulnerability()` analyzes the arguments, verifying that remote execution is indeed possible based on `parser` and the `arguments`, to then open an interactive terminal with `interactive_shell(self)`. Using `query_settings` as the initial variables to structure the `POST` request, running `whoami` as the base command.

```py

def send_request(self, postId="1", command="whoami"):
        headers = {"Content-Type": "application/json"}
        payload_command = f'throw new Exception(`{command}` . "END");'

        base_element = {
            "postId": postId,
            "nonce": self.nonce,
        }

        query_settings = {
            "useQueryEditor": True,
            "queryEditor": payload_command,
        }

        payload_templates = {
            "carousel": {
                **base_element,
                "element": {
                    "name": "carousel",
                    "settings": {"type": "posts", "query": query_settings},
                }
            }
        }
```

Inside the machine, with `ls` I find the `Hidden txt file in a web folder (FLAG)`:

![First Flag](./screenshots/06_Flag_One.png)

It asks what the suspicious process is and suggests using `systemctl | grep "running"`

![First Flag](./screenshots/07_Suspicious_Process.png)

`ubuntu.service TRYHACK3M`, suspicious enough. I run `systemctl cat ubuntu.service`

![Cat Service](./screenshots/08_Investigating_Service.png)

```sh
Restart=on-failure #persistence(?)
WantedBy=multi-user.target #lateral movement(?)
```
It starts from `/lib/NetworkManager/nm-inet-dialog`

![Cat Service](./screenshots/09_Service_Prop.png)

The name of the executable `nm-inet-dialog` is the answer to the second question, and `ubuntu.service` is the answer to the third question.
In short, the `nm-inet-dialog` process is masquerading as `ubuntu.service`.

With `ls -la /lib/NetworkManager/` I investigate what else is in the directory
![Ls Folder](./screenshots/11_ls_dir.png)

Since the suspicious binary is named `-inet-`, I saw `inet.conf` and read it to check whether it was related.

![LogFileFound](./screenshots/12_Miner_log.png)

The malicious activity of the `miner` appears, and `inet.conf` is the name of the `log` file for the miner instance. They also ask for the `address` of the instance (...); scrolling, I see the id:

![Miner ID](./screenshots/13_Miner_ID.png)

`ID:5757314e65474e5962484a4f656d787457544e424e574648555446684d3070735930684b616c70555a7a566b52335276546b686b65575248647a525a57466f77546b64334d6b347a526d685a6255313459316873636b35366247315a4d304531595564476130355864486c6157454a3557544a564e453959556e4a685246497a5932355363303948526a4a6b52464a7a546d706b65466c525054303d`

I look at the characters in the ID and spot numbers and letters ranging from `a - f`, so it is probably in hexadecimal; therefore I analyze it with `CyberChef`:

![CyberChef 1](./screenshots/14_CyberCHef_1.png)

I see that the `output` gives me a value ending in `=`, which usually resembles `base64`; I run it through the base64 filter and again find an ending with `==`, run it through base64 once more, and identify a string that appears to be a cryptocurrency address.

![Wallet ID](./screenshots/15_Wallets.png)

I identify a `bc1` pattern; it looks like there are two wallets. I investigate the first one, `bc1qyk79fcp9hd5kreprce89tkh4wrtl8avt4l67qa` (answer to the fifth question), in `Metasleuth`.


![Metasleuth](./screenshots/16_Wallet_Analysis.png)

I see that it makes transfers to a `KuCoin` wallet, which is also in a `sanctioned` state, so it could contain more information:

![KuCoin Wallet](./screenshots/17_Hacking_Group.png)

Searching for the KuCoin wallet on `google`, I quickly find a link from the U.S. Department of the Treasury that links the wallet address to the `LockBit` ransomware group (answer to the last question)

### by tunlp

![Pwned by tunlp](./screenshots/18_Pwned_tunlp.png)
