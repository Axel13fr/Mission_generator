# Tuto pour ajouter l'extraction d'une donnée au code

Le cas le plus défavorable est celui ou le topic n’est pas encore traité.
Prenons pour exemple, le topic “julienlebg”

## Modification à faire

- Dans **Data_recovery.py** :  
   - Dans **class Drix_data** : 
      - Dans **__init__()** : 
         ajouter le nom du topic dans la liste *self.list_topics*
         ```
         158    self.list_topics = ['/gps', ... , ‘/julienlebg’]
         ```
         ajouter l'attribut pour stocker les données brutes
         ```
         175    self.julienlebg_raw
         ```
      
      - Dans **rosbag2pd()** : 
         ajouter une liste permettant de stocker les fichiers pandas
         ```
         266    julienlebg_pd = []
         ```

