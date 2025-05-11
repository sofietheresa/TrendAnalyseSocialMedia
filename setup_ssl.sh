#!/bin/bash

# Prüfe ob Domain angegeben wurde
if [ -z "$1" ]; then
    echo "Bitte Domain angeben: ./setup_ssl.sh deine-domain.de"
    exit 1
fi

DOMAIN=$1

# Erstelle SSL-Verzeichnis
mkdir -p ssl

# Installiere certbot
apt-get update
apt-get install -y certbot

# Hole SSL-Zertifikat
certbot certonly --standalone -d $DOMAIN

# Kopiere Zertifikate
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/

# Setze Berechtigungen
chmod 644 ssl/fullchain.pem
chmod 644 ssl/privkey.pem

echo "SSL-Zertifikate wurden erfolgreich eingerichtet!" 