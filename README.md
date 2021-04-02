# Mission_generator

Développement d'un outil de génération de rapports de mission basée sur l'analyse des informations capteurs de l'USV Drix 


### Pour lancer le code

Lancer **Data_recovery.py** afin de générer **Mission_report.html** dans le dossier IHM

```
python3 Main.py
```

### Description du dépôt

**mission_report.py**  
Ce script génère un noeud ROS.

**Data_recovery.py**  
Ce script récupère les différents dossiers contenant des rosbags suivant des limites de date et y extrait les données dans des fichiers csv.
Il appelle ensuite des fonctions de Data_process.py et Display.py pour recuillir les données et appelle la fonction d'IHM.py pour générer le rapport de mission.

**Data_process.py**  
Ce Script s'occupe du traitement des données issues des rosbags.

**Display.py**  
Ce Script permet la mise en valeur des données avec la création de graphiques.

**IHM.py**  
Ce Script permet de générer le rapport de mission en format html.



### Dépendances
Les données **gps** sont les données de référence.  
Les données de la **phins** utilisent les données **gps**.  
Les données **gps** sont complétées par des données issues de **mothership_gps** qui pour cela utilise les données **gps**.
