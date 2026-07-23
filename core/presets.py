"""VagrantForge — presets de labs prêts à l'emploi.

Chaque preset est une fonction qui prend le sous-réseau de base et retourne une
config complète. Le frontend web et la CLI partagent exactement ces définitions.
"""


def _vm(nom, box, memoire, cpus, sous_reseau, suffixe_ip, ports=None, script="", **extra):
    vm = {
        "name": nom,
        "box": box,
        "memory": memoire,
        "cpus": cpus,
        "ip": f"{sous_reseau}.{suffixe_ip}" if suffixe_ip else "",
        "synced_folder": f"./{nom}",
        "ports": ports or [],
        "provision": {"type": "shell", "script": script} if script else {"type": "none"},
    }
    vm.update(extra)
    return vm


def preset_k3s(sr="192.168.56"):
    """Cluster K3s : 1 master + 2 workers (Debian)."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("k3s-master", "debian/bookworm64", 2048, 2, sr, 10,
                script="apt-get update -y\ncurl -sfL https://get.k3s.io | sh -\n"
                       "cat /var/lib/rancher/k3s/server/node-token  # token pour joindre les workers\n"),
            _vm("k3s-worker1", "debian/bookworm64", 1536, 1, sr, 11,
                script="apt-get update -y\n"
                       "# Rejoindre : curl -sfL https://get.k3s.io | K3S_URL=https://" + sr + ".10:6443 K3S_TOKEN=<token> sh -\n"),
            _vm("k3s-worker2", "debian/bookworm64", 1536, 1, sr, 12,
                script="apt-get update -y\n"
                       "# Rejoindre : curl -sfL https://get.k3s.io | K3S_URL=https://" + sr + ".10:6443 K3S_TOKEN=<token> sh -\n"),
        ],
    }


def preset_lamp(sr="192.168.56"):
    """Stack LAMP derrière un pare-feu pfSense."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("pfsense", "generic/freebsd14", 1024, 1, sr, 1,
                script="# pfSense : configuration via console/web GUI, pas de shell classique\n"),
            _vm("lamp-server", "debian/bookworm64", 1024, 1, sr, 20,
                ports=[{"guest": 80, "host": 8080}],
                script="apt-get update -y\n"
                       "apt-get install -y apache2 mariadb-server php libapache2-mod-php php-mysql\n"
                       "systemctl enable --now apache2 mariadb\n"),
        ],
    }


def preset_devsecops(sr="192.168.56"):
    """Chaîne CI/CD DevSecOps : GitLab + SonarQube + Vault/monitoring."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("gitlab-ci", "debian/bookworm64", 2048, 2, sr, 30,
                ports=[{"guest": 80, "host": 8090}],
                script="apt-get update -y\n# Runner GitLab CI + configuration à ajouter ici\n"),
            _vm("sonarqube", "debian/bookworm64", 2048, 2, sr, 31,
                ports=[{"guest": 9000, "host": 9000}],
                script="apt-get update -y\n"
                       "# SonarQube exige un vm.max_map_count élevé\nsysctl -w vm.max_map_count=524288\n"),
            _vm("vault-monitoring", "debian/bookworm64", 1536, 1, sr, 32,
                ports=[{"guest": 8200, "host": 8200}, {"guest": 3000, "host": 3000}],
                script="apt-get update -y\n# HashiCorp Vault + Grafana/Prometheus à installer ici\n"),
        ],
    }


def preset_pentest(sr="192.168.56"):
    """Lab de pentest : Kali attaquant + cible Debian volontairement vulnérable."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("kali", "kalilinux/rolling", 3072, 2, sr, 5,
                script="apt-get update -y\n# Kali arrive déjà outillée ; ajoute tes outils ici\n",
                locale="fr_FR.UTF-8", keymap="fr"),
            _vm("cible", "debian/bookworm64", 1024, 1, sr, 6,
                ports=[{"guest": 80, "host": 8081}],
                script="apt-get update -y\n"
                       "# ATTENTION : machine volontairement faible, réseau privé UNIQUEMENT\n"
                       "apt-get install -y apache2 vsftpd\n",
                root_password="toor"),
        ],
    }


def preset_solo(sr="192.168.56"):
    """VM Debian unique, minimale, pour bidouiller vite fait."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("box", "debian/bookworm64", 1024, 1, sr, 10,
                script="apt-get update -y\n"),
        ],
    }


def preset_monitoring(sr="192.168.56"):
    """Stack de supervision : Prometheus + Grafana + Node Exporter."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("prometheus", "debian/bookworm64", 1024, 1, sr, 40,
                ports=[{"guest": 9090, "host": 9090}],
                script="apt-get update -y\n"
                       "apt-get install -y prometheus prometheus-node-exporter\n"
                       "systemctl enable --now prometheus prometheus-node-exporter\n"),
            _vm("grafana", "debian/bookworm64", 1024, 1, sr, 41,
                ports=[{"guest": 3000, "host": 3000}],
                script="apt-get update -y\n"
                       "apt-get install -y apt-transport-https software-properties-common wget\n"
                       "wget -q -O /usr/share/keyrings/grafana.key https://apt.grafana.com/gpg.key\n"
                       "echo 'deb [signed-by=/usr/share/keyrings/grafana.key] "
                       "https://apt.grafana.com stable main' > /etc/apt/sources.list.d/grafana.list\n"
                       "apt-get update -y && apt-get install -y grafana\n"
                       "systemctl enable --now grafana-server\n"
                       "# Source de données Prometheus à ajouter dans Grafana : http://" + sr + ".40:9090\n"),
        ],
    }


def preset_elk(sr="192.168.56"):
    """Stack de logs : Elasticsearch + Logstash + Kibana."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("elasticsearch", "debian/bookworm64", 2560, 2, sr, 50,
                ports=[{"guest": 9200, "host": 9200}],
                script="apt-get update -y\n"
                       "apt-get install -y apt-transport-https gnupg\n"
                       "wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor "
                       "-o /usr/share/keyrings/elastic.gpg\n"
                       "echo 'deb [signed-by=/usr/share/keyrings/elastic.gpg] "
                       "https://artifacts.elastic.co/packages/8.x/apt stable main' "
                       "> /etc/apt/sources.list.d/elastic-8.x.list\n"
                       "apt-get update -y && apt-get install -y elasticsearch\n"
                       "echo 'discovery.type: single-node' >> /etc/elasticsearch/elasticsearch.yml\n"
                       "echo 'xpack.security.enabled: false'  >> /etc/elasticsearch/elasticsearch.yml\n"
                       "systemctl enable --now elasticsearch\n"),
            _vm("kibana", "debian/bookworm64", 1536, 1, sr, 51,
                ports=[{"guest": 5601, "host": 5601}],
                script="apt-get update -y\n"
                       "apt-get install -y apt-transport-https gnupg\n"
                       "wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor "
                       "-o /usr/share/keyrings/elastic.gpg\n"
                       "echo 'deb [signed-by=/usr/share/keyrings/elastic.gpg] "
                       "https://artifacts.elastic.co/packages/8.x/apt stable main' "
                       "> /etc/apt/sources.list.d/elastic-8.x.list\n"
                       "apt-get update -y && apt-get install -y kibana\n"
                       "sed -i 's/#server.host: \"localhost\"/server.host: \"0.0.0.0\"/' "
                       "/etc/kibana/kibana.yml\n"
                       "echo 'elasticsearch.hosts: [\"http://" + sr + ".50:9200\"]' "
                       ">> /etc/kibana/kibana.yml\n"
                       "systemctl enable --now kibana\n"),
        ],
    }


def preset_wordpress(sr="192.168.56"):
    """WordPress + MariaDB sur une seule VM, pour prototyper vite."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("wordpress", "debian/bookworm64", 1536, 1, sr, 60,
                ports=[{"guest": 80, "host": 8082}],
                script="apt-get update -y\n"
                       "apt-get install -y apache2 mariadb-server php php-mysql php-curl php-gd "
                       "php-mbstring php-xml php-zip\n"
                       "systemctl enable --now apache2 mariadb\n"
                       "mysql -e \"CREATE DATABASE wordpress; "
                       "CREATE USER 'wp'@'localhost' IDENTIFIED BY 'wp';\n"
                       "GRANT ALL PRIVILEGES ON wordpress.* TO 'wp'@'localhost'; FLUSH PRIVILEGES;\"\n"
                       "cd /tmp && wget -q https://wordpress.org/latest.tar.gz && tar xzf latest.tar.gz\n"
                       "cp -r wordpress/* /var/www/html/ && chown -R www-data:www-data /var/www/html\n"
                       "# wp-config.php à compléter à la première connexion (DB : wordpress/wp/wp)\n"),
        ],
    }


def preset_gitlab_runner(sr="192.168.56"):
    """GitLab Runner + Docker, pour exécuter des pipelines CI en dehors du SaaS GitLab."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("gitlab-runner", "debian/bookworm64", 2048, 2, sr, 70,
                script="apt-get update -y\n"
                       "apt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\n"
                       "curl -L \"https://gitlab-runner-downloads.s3.amazonaws.com/latest/deb/"
                       "gitlab-runner_amd64.deb\" -o /tmp/gitlab-runner.deb\n"
                       "dpkg -i /tmp/gitlab-runner.deb\n"
                       "# Enregistrement : gitlab-runner register "
                       "--url <url_gitlab> --registration-token <token>\n"),
        ],
    }


def preset_nextcloud(sr="192.168.56"):
    """Nextcloud (stockage/cloud perso) + MariaDB."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("nextcloud", "debian/bookworm64", 2048, 2, sr, 80,
                ports=[{"guest": 443, "host": 8443}, {"guest": 80, "host": 8083}],
                script="apt-get update -y\n"
                       "apt-get install -y apache2 mariadb-server php libapache2-mod-php "
                       "php-mysql php-gd php-curl php-mbstring php-xml php-zip php-intl\n"
                       "systemctl enable --now apache2 mariadb\n"
                       "mysql -e \"CREATE DATABASE nextcloud; "
                       "CREATE USER 'nc'@'localhost' IDENTIFIED BY 'nc';\n"
                       "GRANT ALL PRIVILEGES ON nextcloud.* TO 'nc'@'localhost'; FLUSH PRIVILEGES;\"\n"
                       "cd /tmp && wget -q https://download.nextcloud.com/server/releases/latest.zip\n"
                       "apt-get install -y unzip && unzip -q latest.zip -d /var/www/\n"
                       "chown -R www-data:www-data /var/www/nextcloud\n"),
        ],
    }


def preset_windows_ad(sr="192.168.56"):
    """Lab Windows : contrôleur de domaine Active Directory + poste client.

    Provisioning en PowerShell (WinRM) — VagrantForge bascule automatiquement
    communicateur et script au format Windows dès qu'une box
    `gusztavvargadr/windows-*` est détectée.
    """
    dc = _vm(
        "win-dc", "gusztavvargadr/windows-server", 4096, 2, sr, 90,
        script=(
            "Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools\n"
            "# Puis, en 2e passage (redémarrage requis) :\n"
            "# Install-ADDSForest -DomainName 'lab.local' -InstallDns "
            "-SafeModeAdministratorPassword (ConvertTo-SecureString 'ChangeMoi!2024' -AsPlainText -Force)\n"
        ),
    )
    dc["guest_os"] = "windows"
    dc["winrm_username"] = "vagrant"
    dc["winrm_password"] = "vagrant"
    dc["root_password"] = "ChangeMoi!2024"

    client = _vm(
        "win-client", "gusztavvargadr/windows-11", 4096, 2, sr, 91,
        script=(
            "# Rejoindre le domaine (une fois le DC prêt) :\n"
            "# Add-Computer -DomainName 'lab.local' -Restart\n"
        ),
    )
    client["guest_os"] = "windows"
    client["winrm_username"] = "vagrant"
    client["winrm_password"] = "vagrant"

    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [dc, client],
    }


def preset_hashistack(sr="192.168.56"):
    """Stack HashiCorp : Consul + Vault (serveur) + Nomad (serveur + client)."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("hashi-server", "debian/bookworm64", 2048, 2, sr, 100,
                ports=[{"guest": 8500, "host": 8500}, {"guest": 8200, "host": 8200},
                       {"guest": 4646, "host": 4646}],
                script="apt-get update -y\n"
                       "apt-get install -y gnupg software-properties-common curl lsb-release\n"
                       "curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor "
                       "-o /usr/share/keyrings/hashicorp.gpg\n"
                       "echo \"deb [signed-by=/usr/share/keyrings/hashicorp.gpg] "
                       "https://apt.releases.hashicorp.com $(lsb_release -cs) main\" "
                       "> /etc/apt/sources.list.d/hashicorp.list\n"
                       "apt-get update -y && apt-get install -y consul vault nomad\n"
                       "# Démarrage dev (NON adapté à la prod) :\n"
                       "# consul agent -dev -client 0.0.0.0 &\n"
                       "# vault server -dev -dev-listen-address=0.0.0.0:8200 &\n"
                       "# nomad agent -dev -bind 0.0.0.0 &\n"),
            _vm("hashi-client", "debian/bookworm64", 1536, 1, sr, 101,
                script="apt-get update -y\n"
                       "apt-get install -y gnupg software-properties-common curl lsb-release\n"
                       "curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor "
                       "-o /usr/share/keyrings/hashicorp.gpg\n"
                       "echo \"deb [signed-by=/usr/share/keyrings/hashicorp.gpg] "
                       "https://apt.releases.hashicorp.com $(lsb_release -cs) main\" "
                       "> /etc/apt/sources.list.d/hashicorp.list\n"
                       "apt-get update -y && apt-get install -y consul nomad docker.io\n"
                       "# Rejoindre : nomad agent -client -servers=" + sr + ".100:4647\n"),
        ],
    }


def preset_matomo(sr="192.168.56"):
    """Matomo (analytics web, alternative libre à Google Analytics) + MariaDB."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("matomo", "debian/bookworm64", 1536, 1, sr, 110,
                ports=[{"guest": 80, "host": 8084}],
                script="apt-get update -y\n"
                       "apt-get install -y apache2 mariadb-server php php-mysql php-gd php-curl "
                       "php-mbstring php-xml php-json\n"
                       "systemctl enable --now apache2 mariadb\n"
                       "mysql -e \"CREATE DATABASE matomo; "
                       "CREATE USER 'matomo'@'localhost' IDENTIFIED BY 'matomo';\n"
                       "GRANT ALL PRIVILEGES ON matomo.* TO 'matomo'@'localhost'; FLUSH PRIVILEGES;\"\n"
                       "cd /tmp && wget -q https://builds.matomo.org/matomo-latest.zip\n"
                       "apt-get install -y unzip && unzip -q matomo-latest.zip -d /var/www/\n"
                       "chown -R www-data:www-data /var/www/matomo\n"
                       "# Assistant d'installation web à finir sur http://" + sr + ".110/\n"),
        ],
    }


def preset_minecraft(sr="192.168.56"):
    """Serveur Minecraft Java (vanilla) — pour un lab qui change du DevOps."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("minecraft", "debian/bookworm64", 3072, 2, sr, 120,
                ports=[{"guest": 25565, "host": 25565}],
                script="apt-get update -y\n"
                       "apt-get install -y openjdk-21-jre-headless screen\n"
                       "mkdir -p /opt/minecraft && cd /opt/minecraft\n"
                       "# Remplace l'URL par le lien « server.jar » officiel de la version voulue\n"
                       "# (https://www.minecraft.net/fr-fr/download/server)\n"
                       "wget -q -O server.jar <URL_SERVER_JAR>\n"
                       "echo 'eula=true' > eula.txt\n"
                       "cat > /etc/systemd/system/minecraft.service <<'UNIT'\n"
                       "[Unit]\nDescription=Serveur Minecraft\nAfter=network.target\n"
                       "[Service]\nWorkingDirectory=/opt/minecraft\n"
                       "ExecStart=/usr/bin/java -Xmx2G -Xms1G -jar server.jar nogui\n"
                       "Restart=on-failure\n[Install]\nWantedBy=multi-user.target\nUNIT\n"
                       "systemctl daemon-reload\n"
                       "systemctl enable --now minecraft\n"
                       "# Connexion : " + sr + ".120:25565 (ou 127.0.0.1:25565 en local)\n"),
        ],
    }


def preset_openvpn(sr="192.168.56"):
    """Passerelle VPN OpenVPN (avec easy-rsa), en pont sur le réseau public."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("openvpn-gw", "debian/bookworm64", 1024, 1, sr, 130,
                ports=[{"guest": 1194, "host": 1194}],
                public_network=True,
                script="apt-get update -y\n"
                       "apt-get install -y openvpn easy-rsa\n"
                       "make-cadir /etc/openvpn/easy-rsa\n"
                       "# Génération PKI à finir à la main : ./easyrsa init-pki && "
                       "./easyrsa build-ca ...\n"
                       "echo 1 > /proc/sys/net/ipv4/ip_forward\n"
                       "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf\n"
                       "# Config serveur type dans /etc/openvpn/server.conf (port 1194 udp)\n"),
        ],
    }


def preset_mattermost(sr="192.168.56"):
    """Mattermost (chat d'équipe libre, alternative à Slack) via Docker."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("mattermost", "debian/bookworm64", 2048, 2, sr, 140,
                ports=[{"guest": 8065, "host": 8065}],
                script="apt-get update -y\n"
                       "apt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\n"
                       "mkdir -p /opt/mattermost && cd /opt/mattermost\n"
                       "cat > docker-compose.yml <<'YAML'\n"
                       "services:\n"
                       "  mattermost:\n"
                       "    image: mattermost/mattermost-team-edition:latest\n"
                       "    ports: [\"8065:8065\"]\n"
                       "    volumes: [\"./data:/mattermost/data\"]\n"
                       "YAML\n"
                       "docker compose up -d\n"),
        ],
    }


def preset_redis_cluster(sr="192.168.56"):
    """Cluster Redis à 3 nœuds (mode cluster, réplication automatique)."""
    vms = []
    for i in range(3):
        port = 7000 + i
        vms.append(
            _vm(f"redis-{i}", "debian/bookworm64", 768, 1, sr, 150 + i,
                ports=[{"guest": port, "host": port}],
                script="apt-get update -y\n"
                       "apt-get install -y redis-server\n"
                       f"sed -i 's/^port .*/port {port}/' /etc/redis/redis.conf\n"
                       "sed -i 's/^# cluster-enabled no/cluster-enabled yes/' /etc/redis/redis.conf\n"
                       "sed -i 's/^bind .*/bind 0.0.0.0/' /etc/redis/redis.conf\n"
                       "systemctl restart redis-server\n"
                       "# Une fois les 3 nœuds up, sur l'un d'eux :\n"
                       "# redis-cli --cluster create " + " ".join(
                           f"{sr}.{150 + j}:{7000 + j}" for j in range(3)
                       ) + " --cluster-replicas 0\n"),
        )
    return {"provider": "virtualbox", "box_check_update": False, "vms": vms}


def preset_haproxy_lb(sr="192.168.56"):
    """Répartition de charge : HAProxy + 2 serveurs web backend (round-robin)."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("haproxy", "debian/bookworm64", 1024, 1, sr, 160,
                ports=[{"guest": 80, "host": 8085}],
                script="apt-get update -y\n"
                       "apt-get install -y haproxy\n"
                       "cat >> /etc/haproxy/haproxy.cfg <<'CFG'\n"
                       "\nfrontend front_web\n    bind *:80\n    default_backend back_web\n\n"
                       "backend back_web\n    balance roundrobin\n"
                       f"    server web1 {sr}.161:80 check\n"
                       f"    server web2 {sr}.162:80 check\n"
                       "CFG\n"
                       "systemctl enable --now haproxy && systemctl restart haproxy\n"),
            _vm("web1", "debian/bookworm64", 512, 1, sr, 161,
                script="apt-get update -y\napt-get install -y apache2\n"
                       "echo '<h1>Backend web1</h1>' > /var/www/html/index.html\n"
                       "systemctl enable --now apache2\n"),
            _vm("web2", "debian/bookworm64", 512, 1, sr, 162,
                script="apt-get update -y\napt-get install -y apache2\n"
                       "echo '<h1>Backend web2</h1>' > /var/www/html/index.html\n"
                       "systemctl enable --now apache2\n"),
        ],
    }


def preset_dns_dhcp(sr="192.168.56"):
    """Serveur DNS (BIND9) + DHCP (isc-dhcp-server) et un client pour tester."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("dns-dhcp", "debian/bookworm64", 1024, 1, sr, 170,
                script="apt-get update -y\n"
                       "apt-get install -y bind9 bind9utils isc-dhcp-server\n"
                       "# Zone à déclarer dans /etc/bind/named.conf.local puis /etc/bind/db.lab.local\n"
                       "# Portée DHCP à déclarer dans /etc/dhcp/dhcpd.conf (interface via /etc/default/isc-dhcp-server)\n"
                       "systemctl enable --now bind9\n"
                       "# isc-dhcp-server nécessite sa portée configurée avant de démarrer proprement\n"),
            _vm("client", "debian/bookworm64", 512, 1, sr, 171,
                script="apt-get update -y\n"
                       "# Client pour tester : dig @" + sr + ".170 lab.local ; dhclient -v eth1\n"),
        ],
    }


def preset_wireguard(sr="192.168.56"):
    """Passerelle VPN WireGuard, moderne et légère (alternative à OpenVPN)."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("wireguard-gw", "debian/bookworm64", 512, 1, sr, 180,
                ports=[{"guest": 51820, "host": 51820}],
                public_network=True,
                script="apt-get update -y\n"
                       "apt-get install -y wireguard\n"
                       "umask 077\n"
                       "wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key\n"
                       "cat > /etc/wireguard/wg0.conf <<CFG\n"
                       "[Interface]\nAddress = 10.10.10.1/24\nListenPort = 51820\n"
                       "PrivateKey = $(cat /etc/wireguard/server_private.key)\n"
                       "PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n"
                       "PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n"
                       "# [Peer] à ajouter pour chaque client (clé publique + IP tunnel)\nCFG\n"
                       "echo 1 > /proc/sys/net/ipv4/ip_forward\necho 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf\n"
                       "systemctl enable --now wg-quick@wg0\n"),
        ],
    }


def preset_samba_ad(sr="192.168.56"):
    """Contrôleur de domaine Active Directory via Samba 4 (alternative libre à windows-ad)."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("samba-dc", "debian/bookworm64", 1536, 1, sr, 190,
                script="apt-get update -y\n"
                       "apt-get install -y samba samba-dsdb-modules samba-vfs-modules winbind krb5-config\n"
                       "systemctl stop smbd nmbd winbind 2>/dev/null || true\n"
                       "mv /etc/samba/smb.conf /etc/samba/smb.conf.bak\n"
                       "samba-tool domain provision --use-rfc2307 --realm=LAB.LOCAL --domain=LAB "
                       "--server-role=dc --dns-backend=SAMBA_INTERNAL --adminpass='Vagrant123!' <<< 'yes'\n"
                       "cp /var/lib/samba/private/krb5.conf /etc/krb5.conf\n"
                       "systemctl enable samba-ad-dc && systemctl restart samba-ad-dc\n"
                       "# Test : samba-tool user list  /  kinit administrator@LAB.LOCAL\n"),
            _vm("client", "debian/bookworm64", 512, 1, sr, 191,
                script="apt-get update -y\n"
                       "# Client pour tester la résolution DNS AD : dig @" + sr + ".190 lab.local\n"),
        ],
    }


def preset_reverse_proxy_nginx(sr="192.168.56"):
    """Reverse proxy Nginx en TLS (certificat auto-signé) devant 2 applications backend."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("reverse-proxy", "debian/bookworm64", 1024, 1, sr, 200,
                ports=[{"guest": 443, "host": 8443}, {"guest": 80, "host": 8080}],
                script="apt-get update -y\n"
                       "apt-get install -y nginx openssl\n"
                       "mkdir -p /etc/nginx/ssl\n"
                       "openssl req -x509 -nodes -days 365 -newkey rsa:2048 "
                       "-keyout /etc/nginx/ssl/lab.key -out /etc/nginx/ssl/lab.crt "
                       "-subj '/CN=lab.local'\n"
                       "cat > /etc/nginx/sites-available/reverse-proxy <<CFG\n"
                       "server {\n    listen 443 ssl;\n    server_name lab.local;\n"
                       "    ssl_certificate /etc/nginx/ssl/lab.crt;\n"
                       "    ssl_certificate_key /etc/nginx/ssl/lab.key;\n"
                       f"    location /app1/ {{ proxy_pass http://{sr}.201/; }}\n"
                       f"    location /app2/ {{ proxy_pass http://{sr}.202/; }}\n"
                       "}\nCFG\n"
                       "ln -sf /etc/nginx/sites-available/reverse-proxy /etc/nginx/sites-enabled/\n"
                       "rm -f /etc/nginx/sites-enabled/default\n"
                       "systemctl enable --now nginx && systemctl restart nginx\n"),
            _vm("app1", "debian/bookworm64", 512, 1, sr, 201,
                script="apt-get update -y\napt-get install -y apache2\n"
                       "echo '<h1>App1</h1>' > /var/www/html/index.html\n"
                       "systemctl enable --now apache2\n"),
            _vm("app2", "debian/bookworm64", 512, 1, sr, 202,
                script="apt-get update -y\napt-get install -y apache2\n"
                       "echo '<h1>App2</h1>' > /var/www/html/index.html\n"
                       "systemctl enable --now apache2\n"),
        ],
    }


def preset_nfs_file_server(sr="192.168.56"):
    """Serveur de fichiers NFS partagé avec un client qui monte le partage."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("nfs-server", "debian/bookworm64", 768, 1, sr, 210,
                script="apt-get update -y\n"
                       "apt-get install -y nfs-kernel-server\n"
                       "mkdir -p /srv/partage && chmod 777 /srv/partage\n"
                       f"echo '/srv/partage {sr}.0/24(rw,sync,no_subtree_check,no_root_squash)' >> /etc/exports\n"
                       "exportfs -ra\nsystemctl enable --now nfs-kernel-server\n"),
            _vm("client", "debian/bookworm64", 512, 1, sr, 211,
                script="apt-get update -y\napt-get install -y nfs-common\n"
                       "mkdir -p /mnt/partage\n"
                       f"echo '{sr}.210:/srv/partage /mnt/partage nfs defaults 0 0' >> /etc/fstab\n"
                       "mount -a || true\n"
                       "# Test : ls /mnt/partage\n"),
        ],
    }


def preset_mail_server(sr="192.168.56"):
    """Serveur de messagerie Postfix (SMTP) + Dovecot (IMAP), avec un client de test."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("mail-server", "debian/bookworm64", 1024, 1, sr, 220,
                ports=[{"guest": 25, "host": 2525}, {"guest": 143, "host": 1430}],
                script="export DEBIAN_FRONTEND=noninteractive\n"
                       "apt-get update -y\n"
                       "echo 'postfix postfix/mailname string lab.local' | debconf-set-selections\n"
                       "echo 'postfix postfix/main_mailer_type string Internet Site' | debconf-set-selections\n"
                       "apt-get install -y postfix dovecot-imapd mailutils\n"
                       "postconf -e 'inet_interfaces = all'\n"
                       "systemctl enable --now postfix dovecot\n"
                       "# Créer des utilisateurs Linux = comptes mail (mailbox Maildir par défaut avec Dovecot)\n"
                       "# Test envoi : echo 'corps' | mail -s 'sujet' user@lab.local\n"),
            _vm("client", "debian/bookworm64", 512, 1, sr, 221,
                script="apt-get update -y\napt-get install -y mailutils\n"
                       "# Test : echo 'test' | mail -s 'hello' -S smtp=smtp://" + sr + ".220:25 user@lab.local\n"),
        ],
    }


def preset_squid_proxy(sr="192.168.56"):
    """Proxy web sortant Squid avec ACL, et un client configuré pour l'utiliser."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("squid-proxy", "debian/bookworm64", 768, 1, sr, 230,
                ports=[{"guest": 3128, "host": 3128}],
                script="apt-get update -y\napt-get install -y squid\n"
                       "cat > /etc/squid/conf.d/lab.conf <<CFG\n"
                       "acl lab_net src " + sr + ".0/24\n"
                       "acl sites_autorises dstdomain .lab.local .debian.org\n"
                       "http_access allow lab_net sites_autorises\n"
                       "http_access deny all\n"
                       "CFG\n"
                       "systemctl enable --now squid && systemctl restart squid\n"
                       "# Ajuster sites_autorises selon le besoin du TP (filtrage web)\n"),
            _vm("client", "debian/bookworm64", 512, 1, sr, 231,
                script="apt-get update -y\n"
                       "# Test : http_proxy=http://" + sr + ".230:3128 curl -v http://debian.org\n"),
        ],
    }


def preset_kubeadm(sr="192.168.56"):
    """Cluster Kubernetes complet via kubeadm : 1 control-plane + 2 workers (CNI Calico)."""
    commun = (
        "apt-get update -y\napt-get install -y ca-certificates curl gnupg apt-transport-https\n"
        "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key "
        "| gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg\n"
        "echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] "
        "https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' > /etc/apt/sources.list.d/kubernetes.list\n"
        "curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg\n"
        "echo 'deb [signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian "
        "bookworm stable' > /etc/apt/sources.list.d/docker.list\n"
        "apt-get update -y\napt-get install -y containerd.io kubelet kubeadm kubectl\n"
        "apt-mark hold kubelet kubeadm kubectl\nswapoff -a\n"
        "echo 'overlay\\nbr_netfilter' > /etc/modules-load.d/k8s.conf\nmodprobe overlay\nmodprobe br_netfilter\n"
        "echo 'net.bridge.bridge-nf-call-iptables = 1\\nnet.ipv4.ip_forward = 1' "
        "> /etc/sysctl.d/k8s.conf\nsysctl --system\n"
        "mkdir -p /etc/containerd\ncontainerd config default > /etc/containerd/config.toml\n"
        "sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml\n"
        "systemctl restart containerd\n"
    )
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("k8s-control", "debian/bookworm64", 2560, 2, sr, 15,
                script=commun +
                       "kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address=" + sr + ".15\n"
                       "mkdir -p /root/.kube && cp -i /etc/kubernetes/admin.conf /root/.kube/config\n"
                       "export KUBECONFIG=/root/.kube/config\n"
                       "kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml\n"
                       "kubeadm token create --print-join-command > /vagrant/join-cluster.sh\n"
                       "# Commande de jonction écrite dans join-cluster.sh (dossier partagé) pour les workers\n"),
            _vm("k8s-worker1", "debian/bookworm64", 2048, 2, sr, 16,
                script=commun + "# Rejoindre : bash /vagrant/../k8s-control/join-cluster.sh (ou kubeadm join <ip>:6443 --token ... --discovery-token-ca-cert-hash ...)\n"),
            _vm("k8s-worker2", "debian/bookworm64", 2048, 2, sr, 17,
                script=commun + "# Rejoindre : bash /vagrant/../k8s-control/join-cluster.sh (ou kubeadm join <ip>:6443 --token ... --discovery-token-ca-cert-hash ...)\n"),
        ],
    }


def preset_jenkins(sr="192.168.56"):
    """Chaîne CI/CD Jenkins : contrôleur + agent Docker relié en SSH."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("jenkins-controller", "debian/bookworm64", 2048, 2, sr, 240,
                ports=[{"guest": 8080, "host": 8080}, {"guest": 50000, "host": 50000}],
                script="apt-get update -y\napt-get install -y openjdk-17-jre-headless curl gnupg\n"
                       "curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key "
                       "| gpg --dearmor -o /usr/share/keyrings/jenkins.gpg\n"
                       "echo 'deb [signed-by=/usr/share/keyrings/jenkins.gpg] "
                       "https://pkg.jenkins.io/debian-stable binary/' > /etc/apt/sources.list.d/jenkins.list\n"
                       "apt-get update -y && apt-get install -y jenkins\nsystemctl enable --now jenkins\n"
                       "# Mot de passe admin initial : cat /var/lib/jenkins/secrets/initialAdminPassword\n"),
            _vm("jenkins-agent", "debian/bookworm64", 1536, 1, sr, 241,
                script="apt-get update -y\napt-get install -y openjdk-17-jre-headless curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\nusermod -aG docker vagrant\n"
                       "# Agent à relier en SSH depuis Jenkins (Manage Nodes) : IP " + sr + ".241, user vagrant\n"),
        ],
    }


def preset_borg_backup(sr="192.168.56"):
    """Serveur de sauvegarde BorgBackup (SSH) + client planifié par cron."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("backup-server", "debian/bookworm64", 1024, 1, sr, 250,
                script="apt-get update -y\napt-get install -y borgbackup openssh-server\n"
                       "mkdir -p /srv/borg-repos && chown vagrant:vagrant /srv/borg-repos\n"
                       "su - vagrant -c \"borg init --encryption=repokey-blake2 /srv/borg-repos/lab\"\n"
                       "# Clé SSH du client à ajouter dans /home/vagrant/.ssh/authorized_keys\n"),
            _vm("backup-client", "debian/bookworm64", 768, 1, sr, 251,
                script="apt-get update -y\napt-get install -y borgbackup\n"
                       "su - vagrant -c \"ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519 -q\"\n"
                       "cat > /usr/local/bin/sauvegarde-quotidienne.sh <<'SCRIPT'\n#!/bin/sh\n"
                       "export BORG_REPO=ssh://vagrant@" + sr + ".250/srv/borg-repos/lab\n"
                       "borg create --stats --compression zstd ::'{hostname}-{now}' /etc /var/www 2>/dev/null\n"
                       "borg prune --keep-daily=7 --keep-weekly=4 --keep-monthly=6\nSCRIPT\n"
                       "chmod +x /usr/local/bin/sauvegarde-quotidienne.sh\n"
                       "echo '0 2 * * * root /usr/local/bin/sauvegarde-quotidienne.sh' > /etc/cron.d/borg-backup\n"
                       "# Copier la clé publique client (~/.ssh/id_ed25519.pub) vers authorized_keys du serveur avant le premier run\n"),
        ],
    }


def preset_gitea(sr="192.168.56"):
    """Serveur Git auto-hébergé Gitea (alternative légère à GitLab) via Docker."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("gitea", "debian/bookworm64", 1024, 1, sr, 245,
                ports=[{"guest": 3000, "host": 3300}, {"guest": 22, "host": 2222}],
                script="apt-get update -y\napt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\nmkdir -p /opt/gitea && cd /opt/gitea\n"
                       "cat > docker-compose.yml <<'YAML'\nservices:\n  gitea:\n"
                       "    image: gitea/gitea:latest\n    environment:\n      - USER_UID=1000\n"
                       "      - USER_GID=1000\n    ports: [\"3000:3000\", \"2222:22\"]\n"
                       "    volumes: [\"./data:/data\"]\nYAML\ndocker compose up -d\n"
                       "# Assistant d'installation web sur http://" + sr + ".245:3000/ (première connexion)\n"),
        ],
    }


def preset_github_runner(sr="192.168.56"):
    """Runner GitHub Actions auto-hébergé, avec Docker pour les jobs conteneurisés."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("github-runner", "debian/bookworm64", 2048, 2, sr, 252,
                script="apt-get update -y\napt-get install -y curl ca-certificates tar\n"
                       "curl -fsSL https://get.docker.com | sh\nusermod -aG docker vagrant\n"
                       "mkdir -p /opt/actions-runner && cd /opt/actions-runner\n"
                       "# Version/URL à adapter (voir la page « Add runner » du dépôt/organisation GitHub) :\n"
                       "curl -o runner.tar.gz -L "
                       "https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64.tar.gz\n"
                       "tar xzf runner.tar.gz && chown -R vagrant:vagrant /opt/actions-runner\n"
                       "# Puis en tant que vagrant : ./config.sh --url https://github.com/<org>/<repo> "
                       "--token <TOKEN_ENREGISTREMENT>\n"
                       "# Et : sudo ./svc.sh install && sudo ./svc.sh start\n"),
        ],
    }


def preset_awx(sr="192.168.56"):
    """AWX (Ansible Tower libre) via Docker Compose, pour piloter des playbooks depuis une interface web."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("awx", "debian/bookworm64", 4096, 2, sr, 253,
                ports=[{"guest": 80, "host": 8087}],
                script="apt-get update -y\napt-get install -y curl ca-certificates git\n"
                       "curl -fsSL https://get.docker.com | sh\n"
                       "mkdir -p /opt/awx && cd /opt/awx\n"
                       "git clone -b 23.5.1 --depth 1 https://github.com/ansible/awx.git src\n"
                       "# Déploiement via awx-operator (Kubernetes) recommandé en prod ; pour un lab, voir\n"
                       "# le docker-compose de développement documenté dans src/tools/docker-compose/\n"
                       "# Interface une fois lancée : http://" + sr + ".253/\n"),
        ],
    }


def preset_duplicati(sr="192.168.56"):
    """Duplicati : sauvegarde chiffrée avec interface web, planification intégrée (complément GUI à borg-backup)."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("duplicati", "debian/bookworm64", 1024, 1, sr, 254,
                ports=[{"guest": 8200, "host": 8200}],
                script="apt-get update -y\napt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\nmkdir -p /opt/duplicati && cd /opt/duplicati\n"
                       "cat > docker-compose.yml <<'YAML'\nservices:\n  duplicati:\n"
                       "    image: duplicati/duplicati:latest\n    ports: [\"8200:8200\"]\n"
                       "    volumes:\n      - \"./config:/config\"\n      - \"./backups:/backups\"\n"
                       "      - \"/etc:/source/etc:ro\"\n      - \"/var/www:/source/var-www:ro\"\nYAML\n"
                       "docker compose up -d\n"
                       "# Interface web (assistant de sauvegarde) sur http://" + sr + ".254:8200/\n"),
        ],
    }


def preset_docker_swarm(sr="192.168.56"):
    """Cluster Docker Swarm : 1 manager + 2 workers — orchestration plus légère que kubeadm/k3s."""
    return {
        "provider": "virtualbox",
        "box_check_update": False,
        "vms": [
            _vm("swarm-manager", "debian/bookworm64", 1536, 1, sr, 203,
                ports=[{"guest": 8080, "host": 8088}],
                script="apt-get update -y\napt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\nusermod -aG docker vagrant\n"
                       "docker swarm init --advertise-addr " + sr + ".203\n"
                       "docker swarm join-token worker -q > /vagrant/swarm-join-token.txt\n"
                       "# Token de jonction écrit dans swarm-join-token.txt (dossier partagé) pour les workers\n"
                       "# Exemple de service : docker service create --name web --replicas 3 -p 8080:80 nginx\n"),
            _vm("swarm-worker1", "debian/bookworm64", 1024, 1, sr, 204,
                script="apt-get update -y\napt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\nusermod -aG docker vagrant\n"
                       "# Rejoindre : docker swarm join --token $(cat /vagrant/../swarm-manager/swarm-join-token.txt) "
                       + sr + ".203:2377\n"),
            _vm("swarm-worker2", "debian/bookworm64", 1024, 1, sr, 205,
                script="apt-get update -y\napt-get install -y curl ca-certificates\n"
                       "curl -fsSL https://get.docker.com | sh\nusermod -aG docker vagrant\n"
                       "# Rejoindre : docker swarm join --token $(cat /vagrant/../swarm-manager/swarm-join-token.txt) "
                       + sr + ".203:2377\n"),
        ],
    }


PRESETS = {
    "solo":           ("VM Debian unique", preset_solo),
    "k3s":            ("Cluster K3s (3 VMs)", preset_k3s),
    "lamp":           ("LAMP + pfSense", preset_lamp),
    "devsecops":      ("Chaîne CI/CD DevSecOps", preset_devsecops),
    "pentest":        ("Lab pentest Kali + cible", preset_pentest),
    "monitoring":     ("Prometheus + Grafana", preset_monitoring),
    "elk":            ("Elasticsearch + Kibana", preset_elk),
    "wordpress":      ("WordPress + MariaDB", preset_wordpress),
    "gitlab-runner":  ("GitLab Runner + Docker", preset_gitlab_runner),
    "nextcloud":      ("Nextcloud + MariaDB", preset_nextcloud),
    "windows-ad":     ("Windows : DC Active Directory + client", preset_windows_ad),
    "hashistack":     ("HashiCorp : Consul + Vault + Nomad", preset_hashistack),
    "matomo":         ("Matomo — analytics web libre", preset_matomo),
    "minecraft":      ("Serveur Minecraft Java", preset_minecraft),
    "openvpn":        ("Passerelle VPN OpenVPN", preset_openvpn),
    "mattermost":     ("Mattermost — chat d'équipe (Docker)", preset_mattermost),
    "redis-cluster":  ("Cluster Redis à 3 nœuds", preset_redis_cluster),
    "haproxy-lb":     ("Répartition de charge HAProxy", preset_haproxy_lb),
    "dns-dhcp":       ("Serveur DNS/DHCP (BIND9 + isc-dhcp)", preset_dns_dhcp),
    "wireguard":      ("Passerelle VPN WireGuard", preset_wireguard),
    "samba-ad":       ("Contrôleur AD via Samba 4", preset_samba_ad),
    "reverse-proxy-nginx": ("Reverse proxy Nginx TLS", preset_reverse_proxy_nginx),
    "nfs-file-server": ("Serveur de fichiers NFS", preset_nfs_file_server),
    "mail-server":    ("Messagerie Postfix + Dovecot", preset_mail_server),
    "squid-proxy":    ("Proxy web sortant Squid", preset_squid_proxy),
    "kubeadm":        ("Kubernetes complet (kubeadm + Calico)", preset_kubeadm),
    "jenkins":        ("CI/CD Jenkins — contrôleur + agent Docker", preset_jenkins),
    "borg-backup":    ("Sauvegarde BorgBackup (serveur + client planifié)", preset_borg_backup),
    "gitea":          ("Serveur Git Gitea (alternative légère à GitLab)", preset_gitea),
    "github-runner":  ("Runner GitHub Actions auto-hébergé", preset_github_runner),
    "awx":            ("AWX — Ansible Tower libre (automatisation)", preset_awx),
    "duplicati":      ("Duplicati — sauvegarde chiffrée avec interface web", preset_duplicati),
    "docker-swarm":   ("Cluster Docker Swarm (manager + 2 workers)", preset_docker_swarm),
}


def obtenir_preset(nom, sous_reseau="192.168.56"):
    """Retourne la config d'un preset par son nom, ou lève KeyError."""
    if nom not in PRESETS:
        raise KeyError(nom)
    return PRESETS[nom][1](sous_reseau)
