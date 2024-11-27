# Outils WIN11

## CTRL + SHIF + R
* Plein écran

## Montage
* Clipchamp



# OBS


# Étapes principales :

1. **Installer et configurer OBS :**
   - Téléchargez OBS depuis [le site officiel](https://obsproject.com).
   - Lors du premier lancement, utilisez l'assistant de configuration automatique (Auto-Configuration Wizard). Choisissez l’option "Optimiser pour l’enregistrement, je ne fais pas de streaming".

2. **Configurer les sources dans OBS :**
   - Cliquez sur le bouton **"+"** dans la section **Sources**.
   - **Ajouter une capture d’écran :**
     - Sélectionnez "Capture d’écran" (ou "Display Capture") pour enregistrer tout ce qui est affiché sur votre écran.
     - Si vous utilisez plusieurs écrans, choisissez celui où se trouve votre projet.
   - **Ajouter une capture audio :**
     - Cliquez sur **"+"**, puis "Capture audio entrée".
     - Sélectionnez le microphone que vous souhaitez utiliser.
     - Testez votre micro dans les paramètres audio pour vérifier qu’il capte correctement le son.

3. **Ajuster les paramètres vidéo et audio :**
   - Allez dans **Fichier > Paramètres > Vidéo**.
     - Définissez la **Résolution de base** (celle de votre écran, par exemple 1920x1080 si Full HD).
     - Choisissez une **Résolution de sortie** (idem ou légèrement réduite pour alléger le fichier, comme 1280x720 pour YouTube).
     - Définissez une fréquence d’image (FPS) de 30 pour un bon compromis entre qualité et fluidité.
   - Allez dans **Fichier > Paramètres > Sortie > Enregistrement** :
     - Format : MP4 (idéal pour YouTube).
     - Codec : x264 (par défaut).
     - Débit vidéo : 6000 kbps pour 1080p ou 3000 kbps pour 720p.

4. **Enregistrer votre projet Python :**
   - Assurez-vous que votre projet est prêt à être affiché.
   - Lancez l’enregistrement en cliquant sur **"Démarrer l’enregistrement"** dans OBS.
   - Effectuez votre démonstration, commentez votre code ou votre application en direct.

5. **Arrêter l’enregistrement :**
   - Une fois terminé, cliquez sur **"Arrêter l’enregistrement"**.
   - Le fichier sera enregistré dans le dossier spécifié dans les paramètres (par défaut dans le dossier Vidéos).

6. **Modifier et publier sur YouTube :**
   - Si nécessaire, utilisez un logiciel simple comme Shotcut ou iMovie pour couper les parties inutiles.
   - Connectez-vous à YouTube, cliquez sur "Créer > Importer des vidéos", ajoutez votre fichier, puis remplissez les informations requises (titre, description, etc.).

# Conseils supplémentaires :
- **Temps limité d’enregistrement :** Faites des essais pour vous familiariser avec OBS avant d’enregistrer la version finale.
- **Résolution de votre écran :** Si vous utilisez un écran Full HD (1920x1080), cela suffit pour une vidéo de bonne qualité sur YouTube. Indiquez-moi votre résolution si elle est différente, pour ajuster les paramètres.
- **Microphone externe :** Si possible, utilisez un bon micro pour un son plus clair.




Avec une résolution de **2560x1600**, voici les paramètres ajustés pour OBS afin d'optimiser votre enregistrement :

# Paramètres spécifiques pour votre résolution

1. **Paramètres vidéo dans OBS :**
   - **Résolution de base (canvas)** : **2560x1600** (correspond à votre écran).
   - **Résolution de sortie (scaled)** : 
     - **1920x1200** pour un bon compromis entre qualité et taille (16:10 correspond à votre ratio d'écran).
     - Si vous voulez conserver la pleine résolution pour un rendu de meilleure qualité sur YouTube, utilisez **2560x1600**.
   - **Fréquence d’images (FPS)** : **30 FPS** (recommandé pour des présentations de projets).

2. **Paramètres de sortie dans OBS :**
   - Allez dans **Fichier > Paramètres > Sortie > Enregistrement**.
   - **Type d'enregistrement** : Standard.
   - **Chemin d'enregistrement** : Sélectionnez un dossier accessible.
   - **Format d’enregistrement** : **MP4** (recommandé pour YouTube).
   - **Codec vidéo** : **x264**.
   - **Débit vidéo (Bitrate)** :
     - Pour 1920x1200 : **6000 à 8000 kbps**.
     - Pour 2560x1600 : **12000 à 14000 kbps** (fichiers plus volumineux mais meilleure qualité).

3. **Paramètres audio :**
   - Allez dans **Fichier > Paramètres > Audio** :
     - **Taux d’échantillonnage** : 48 kHz.
     - **Bitrate audio** : 192 kbps.
   - Vérifiez la qualité de votre microphone dans le **Mixer Audio** d’OBS.

4. **Équilibrer la qualité et la fluidité :**
   - Si votre ordinateur a des performances limitées, vous pouvez :
     - Réduire la résolution de sortie à **1600x1000**.
     - Réduire légèrement le bitrate vidéo (par exemple, 5000 kbps pour 1920x1200).



# Workflow recommandé

1. **Préparation avant enregistrement :**
   - Réglez les fenêtres pour qu’elles soient visibles et claires.
   - Ajustez les polices pour que le texte soit lisible dans la vidéo (taille de police 16 ou supérieure).
   - Si besoin, masquez les barres inutiles (applications ouvertes, notifications, etc.).

2. **Configuration dans OBS :**
   - Ajoutez les **Sources** nécessaires :
     - **Capture d’écran** : Montre tout l’écran.
     - **Capture audio entrée** : Pour enregistrer votre narration.
     - Facultatif : Ajoutez une webcam (capture vidéo) si vous souhaitez apparaître.

3. **Enregistrement :**
   - Lancez l’enregistrement depuis OBS, effectuez votre démonstration.
   - Vérifiez que votre narration est claire et que tout est visible.

4. **Compression et mise en ligne :**
   - Si le fichier est volumineux, utilisez un logiciel comme **HandBrake** pour réduire la taille sans perdre en qualité.
   - Sur YouTube :
     - Pour 1920x1200, choisissez "1080p".
     - Pour 2560x1600, choisissez "1440p".


# Exemple de réglages rapides pour votre cas :
- **Canvas** : 2560x1600
- **Sortie vidéo** : 1920x1200
- **FPS** : 30
- **Bitrate vidéo** : 8000 (1920x1200)
- **Format** : MP4 avec codec x264

