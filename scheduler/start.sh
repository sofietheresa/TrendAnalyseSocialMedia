#!/bin/bash

# .env-Variablen exportieren
printenv > /etc/environment

# Cron-Log vorbereiten
touch /var/log/cron.log

# Cron starten
cron

# Cron-Log anzeigen (damit 'docker logs' etwas sieht)
tail -f /var/log/cron.log
