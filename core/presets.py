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


PRESETS = {
    "solo":      ("VM Debian unique", preset_solo),
    "k3s":       ("Cluster K3s (3 VMs)", preset_k3s),
    "lamp":      ("LAMP + pfSense", preset_lamp),
    "devsecops": ("Chaîne CI/CD DevSecOps", preset_devsecops),
    "pentest":   ("Lab pentest Kali + cible", preset_pentest),
}


def obtenir_preset(nom, sous_reseau="192.168.56"):
    """Retourne la config d'un preset par son nom, ou lève KeyError."""
    if nom not in PRESETS:
        raise KeyError(nom)
    return PRESETS[nom][1](sous_reseau)
