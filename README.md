# Mission_generator

Développement d'un outil de génération de rapports de mission basée sur l'analyse des informations capteurs de l'USV Drix 


### Pour lancer le code

Lancer **Data_recovery.py** afin de générer **Mission_report.html** dans le dossier IHM

```
python3 Data_recovery.py
```

### Description du dépôt

**mission_report.py**  
Ce script génère un noeud ROS.

**Data_recovery.py**  
Ce script récupère les différents dossiers contenant des rosbags suivant des limites de date et y extrait les données.
