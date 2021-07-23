# Mission_generator

Développement d'un outil de génération de rapports de mission basée sur l'analyse des informations capteurs de l'USV Drix 


### Description du dépôt

Le projet est divisé en 2 parties :
-	une partie PC DriX
- une partie PC Survey

La partie PC DriX composée de **Data_recovery.py, Data_process.py, mission_report.py** permet de récupérer les Rosbags, de les traiter et de les compresser dans un fichier.
Ce fichier est transmis à la partie PC Survey composée de **Data_collecting.py, Display.py, IHM.py, main.py** qui va décompresser le fichier, récupérer son contenue et créer une IHM pour le mettre en page.



### Partie PC DriX

**Data_recovery.py**
Ce script récupère les différents dossiers contenant des rosbags suivant des limites de date et y extrait les données dans des fichiers csv. Il appelle ensuite des fonctions de **Data_process.py** pour traiter les données. Ce code est le code principal de la partie PC DriX.  
/!\ Pour pouvoir faire fonctionner ce code, il faut avant tout avoir sourcer le terminal pour avec accès aux définitions des msg ROS
```
source ~/ros_ws/devel/setup.zsh
```
puis on lance le code en ayant préalablement changé les valeurs des variables du code (date_d, date_f, path) l 885 afin de paramétrer le rapport de mission.
```
python3 Data_recovery.py
```


