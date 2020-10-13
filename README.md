# PyDriveSync


1. Create Account

Créer un projet sur https://console.developers.google.com/projectcreate
Activer l'API Google Drive via : https://console.developers.google.com/apis/library pour ce projet
Créer ecran d'autorisation Oauth : https://console.developers.google.com/apis/credentials/consent
Créer des identifiants : https://console.developers.google.com/apis/credentials/oauthclient
Type d'application : application de bureau, nom : pydrivesync

Sauvegarder l'ID Client et le code secret client

2. Configuration pydrivesync

pip3 install pydrivesync.whl

pydrivesync /var/www/drive/data/chef/files/

0 0 * * * sudo chroot debian_amd64/ pydrivesync /var/www/drive/data/chef/files/
0 1 * * * sudo chroot debian_amd64/ chown -R www-data /var/www/drive/data/chef/files/
