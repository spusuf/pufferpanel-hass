# Pufferpanel Home Assistant integration

This integration allows monitoring and control of Pufferpanel game servers.

![Preview of game server status and control functionality in Home Assistant](https://github.com/spusuf/pufferpanel-hass/blob/main/preview/preview1.png "Preview 1")

Provides the following for all servers:
* Status (Online, Offline, Installing)
* CPU usage (thread, 100% utilisation of 4 threads will show as 400% as Linux standard)
* CPU usage (total, 100% utilisation of 4 threads will show as 100%, uses thread count set during integration configuration)
* IP address (uses the same host as configured if 127.0.0.1, 0.0.0.0, localhost)
* Game port (Public port, docker internal port may differ)
* Auto start (on node boot) enabled
* Restart on (server) crash enabled
* Start (button)
* Stop (button)
* Restart (button)
* Install (/reinstall/update) button
* Reload (game configuration) button
* Kill server (if stop is not responding)
* Node name (if not local)

Provides the following for Minecraft servers:
* Players online
* Mod launcher (Vanilla, NeoForge, Paper, etc)
* Game version
* Server message (MOTD)



## Installation
1. Getting your authentication from pufferpanel
    1. Go to your pufferpanel IP
    2. Log in to your pufferpanel
    3. Click on your user icon (at least for 3.x)
    4. Click on OAuth2 Clients
    5. Click Create new OAuth2 Client
    6. Name it HomeAssistant (or anything you want)
    7. Copy BOTH Client ID and Client Secret (you can see Client ID again but Secret will never be shown again)
2. Install the integration
    1. Use the IP of your pufferpanel machine's network interface
    2. Use the Port of pufferpanel (it is 8080 by default)
    3. Use the Client ID you got from pufferpanel
    4. Use the Client Secret you got from pufferpanel
    5. Enable Use HTTPS **ONLY** if you are connecting via a domain with a SSL certificate (leave this off unless you know you need it)
    6. Refresh interval (15 seconds minimum, 30 or 60 is reasonable)
    7. Define how many CPU Threads the host has (not cores, you can use `lscpu` and use the number of online cpus) 

Done! 

You only need to connect to your pufferpanel host once and all game servers across all nodes are automatically added.

![Preview of multiple game servers in Home Assistant](https://github.com/spusuf/pufferpanel-hass/blob/main/preview/preview2.png "Preview 2")



## Notes
Not affiliated with the Home Assistant nor Pufferpanel teams.

I was personally upset that the easiest to use self hosted game server manager was not compatible with my all in one home dashboards, so I took it upon myself as an exercise.

This is my first custom integration and I am not a professional python developer so if there are any errors or inefficiencies in my code feel free to write a PR or message me on discord (same name as github).

Here's what is POSSIBLE using the Pufferpanel API:
* Trigger manual backup (but requires server to be offline)
* Get console logs
* Publish commands to console
* Get SFTP port (Does not appear to deviate from 5657)
* Get SFTP hostname (IP + server ID)
* Change Minecraft configuration including max players and MOTD

These are not planned due to time constraints, there may be even more options in the API, it is documented at pufferpanel_ip:port/swagger/index.html

Also sorry about the oversaturated screenshot, HDR screenshots on Hyprland isn't perfect yet :P
