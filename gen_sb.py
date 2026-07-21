import json, sys

auth = sys.argv[1]
host = sys.argv[2]
port = int(sys.argv[3])
peer = sys.argv[4]
insecure = sys.argv[5].lower() == 'true'

config = {
    "log": {"level": "info"},
    "inbounds": [{
        "type": "mixed", "tag": "mixed-in",
        "listen": "127.0.0.1", "listen_port": 1080,
        "sniff": True, "sniff_override_destination": True
    }],
    "outbounds": [{
        "type": "hysteria2", "tag": "hysteria2-out",
        "server": host, "server_port": port,
        "password": auth,
        "tls": {"enabled": True, "server_name": peer, "insecure": insecure}
    }],
    "route": {"final": "hysteria2-out"}
}

print(json.dumps(config, indent=2))