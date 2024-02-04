<h1 align="center">Project NAM
<h3 align="center">Self hosted architecture for communication with Open AI</h3>
<p>You are currently viewing a <b>client</b>. You can use <b>client</b> to connect to nam server:</p>
<p><b>+ download server</b>  -  https://github.com/Ivashkka/nam</p>
<br>
<p><b>install:</b></p>
<p>install make package:</p>
<p><code>apt install make</code></p>
<p>create directory for clonning git repo on your machine:</p>
<p><code>cd ~</code></p>
<p><code>mkdir nam_repos; cd nam_repos</code></p>
<p>clone nam_client repo:</p>
<p><code>git clone https://github.com/Ivashkka/nam_client.git</code></p>
<p><code>cd nam_client</code></p>
<p>start make install from root:</p>
<p><code>sudo make install</code></p>
<p>wait until instalation finishes</p>
<p>after installation is complete you can start nam_client:</p>
<p><code>systemctl start nam_client</code></p>
<p><code>systemctl status nam_client</code></p>
<p>and enable if needed:</p>
<p><code>systemctl enable nam_client</code></p>
<br>
<p><b>settings:</b>
<p>all client settings located in /etc/nam_client</p>
<p>conf.yaml - primary config file</p>
<p>edit ip and port to connect to in conf.yaml</p>
<p>auth.json - file to store auth data</p>
<br>
<p><b>usage:</b>
<p>to interact with client - use nam instrument</p>
<p>use <code>nam - help</code> to get info about any commands</p>
<p>use <code>nam some_question</code> to ask question</p>
<p>note: do not use nam inside nam_client git repo directory(where you cloned nam_client.git), this can lead to bugs</p>
<br>
<p><b>uninstall:</b>
<p>stop client:</p>
<p><code>systemctl stop nam_client</code></p>
<p>or use <code>nam - stop</code></p>
<p>disable autorun if needed:</p>
<p><code>systemctl disable nam_client</code></p>
<p>move inside nam_client git repo directory(where you cloned nam_client.git):</p>
<p><code>cd ~/nam_repos/nam_client</code></p>
<p>start uninstall process:</p>
<p><code>make clean</code></p>
<br>
<p>note: latest version is - v1.0.0unstable. There may be a few bugs</p>
