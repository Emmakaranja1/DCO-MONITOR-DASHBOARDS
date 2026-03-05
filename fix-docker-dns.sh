set -e

CONFIG_DIR="/etc/docker"
CONFIG_FILE="$CONFIG_DIR/daemon.json"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_CONFIG="$SCRIPT_DIR/docker-daemon.json"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo $0"
  exit 1
fi

if [ -f "$CONFIG_FILE" ]; then
  BACKUP="$CONFIG_FILE.bak.$(date +%Y%m%d_%H%M%S)"
  echo "Backing up to $BACKUP"
  cp "$CONFIG_FILE" "$BACKUP"
fi

mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_FILE" ] && [ -s "$CONFIG_FILE" ]; then
  python3 -c "
import json
path = '$CONFIG_FILE'
try:
    with open(path) as f:
        d = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    d = {}
d['dns'] = ['8.8.8.8', '8.8.4.4']
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
print('DNS config applied')
" || cp "$PROJECT_CONFIG" "$CONFIG_FILE"
else
  cp "$PROJECT_CONFIG" "$CONFIG_FILE"
  echo "DNS config written"
fi

echo "Restarting Docker..."
systemctl restart docker

echo "Done. Rebuild with: docker-compose build --no-cache dco-exporter && docker-compose up -d"
