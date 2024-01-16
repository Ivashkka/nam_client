<h1 align="center">Project NAM
<h3 align="center">Self hosted architecture for communication with Open AI</h3>
<p>You are currently viewing a <b>client</b>. You can use <b>client</b> to connect to nam server:
<p><b>+ download server</b>  -  https://github.com/Ivashkka/nam
<p>
<p><b>install:</b>
<p>create directory for clonning git repo on your machine:
<p>cd ~
<p>mkdir nam_repos; cd nam_repos
<p>clone nam_client repo:
<p>git clone https://github.com/Ivashkka/nam_client.git
<p>cd nam_client
<p>start make install from root
<p>sudo make install
<p>wait until instalation finishes
<p>after installation is complete you can start nam_client:
<p>systemctl start nam_client
<p>systemctl status nam_client
<p>and enable if needed:
<p>systemctl enable nam_client
<p>
<p><b>settings:</b>
<p>all client settings located in /etc/nam_client
<p>conf.yaml - primary config file
<p>edit ip and port to connect to in conf.yaml
<p>auth.json - file to store auth data
<p>
<p><b>usage:</b>
<p>to interact with client - use nam instrument
<p>use nam - help to get info about any commands
<p>use nam question to ask question
<p>note: do not use nam inside nam_client git repo directory(where you cloned nam_client.git), this can lead to bugs
<p>
<p><b>uninstall:</b>
<p>stop client:
<p>systemctl stop nam_client
<p>or use nam - stop
<p>disable autorun if needed:
<p>systemctl disable nam_client
<p>move inside nam_client git repo directory(where you cloned nam_client.git):
<p>cd ~/nam_repos/nam_client
<p>start uninstall process:
<p>make clean
<p>
<p>note: latest version is - v1.0.0unstable. There may be a few bugs
