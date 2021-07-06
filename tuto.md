# Tuto pour ajouter l'extraction d'une donnée au code

Le cas le plus défavorable est celui ou le topic n’est pas encore traité.
Prenons pour exemple, le topic “julienlebg”

## Modification à faire

ajouter l'import du msg ROS permettant de lire les nouvelles données
```
20    from ENSTA.msg import Roboticien
```

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
         
      - Dans **result_path_setup()** : 
         ajouter la création du dossier qui va contenir le fichier .csv
         ```
         218    os.makedirs(self.result_path + '/julienlebg')
         ```
         
      - Dans **rosbag2pd()** : 
         ajouter une liste permettant de stocker les fichiers pandas
         ```
         266    julienlebg_pd = []
         ```
         ajouter un dictionnaire permettant de stoker les données issues du rosbag
         ```
         297    dic_julienlebg = {‘Time’ : [], ‘donnee1’ : [], ‘donnee2’ : [], ‘ect’ : []}
         ```
         puis dans la boucle for lisant les rosbags ajouter l'extraction des données du topic
         ```
         330    if topic == 'julienlebg':
         331         m:Roboticien = msg
         332         dic_julienlebg['Time'].append(time)
         333         dic_julienlebg['donnee1'].append(m.donnée1)
         334         dic_julienlebg['donnee2'].append(m.donnée2)
         335         dic_julienlebg['ect'].append(m.ect)
         ```
         puis on stocke chaque variable pandas dans la liste
         ```
         570    if dic_julienlebg['Time']:
         571         julienlebg_pd.append(pd.DataFrame.from_dict(dic_julienlebg))
         ```
         on ajoute la concaténation des variables pandas
         ```
         685    if len(julienlebg_pd) > 0:
         686         self.julienlebg_raw = pd.concat(julienlebg_pd, ignore_index=True)
         687         print3000("Julienlebg data imported : " + str(len(julienlebg_pd)) + '/' + str(len(L_bags)))
         688    else:
         689         print3000('Error, no Julienlebg data found')
         ```
   - Dans **code_launcher** : 
      ajouter l'appel de la fonction permettant de traiter la nouvelle donnée
      ```
      860    if Data.julienlebg_raw is not None:
      861         Dp.extract_julienlebg_data(Data)
      862         print("Julienlebg data processed")  
      ```  
      
       

- Dans **Data_process.py** : 
   ajouter une nouvelle fonction permettant de traiter la donnée en utilisant les différents outils développés...
   ```
   772    def extract_julienlebg_data(Data):
   773         path = Data.result_path + "/julienlebg"
   774         df = Data.julienlebg_raw
   775
   776         report_topic_heading('julienlebg', df.shape)
   777
   778         df1 = data_reduced(df, 'donnee1', path)
   779         df2 = noisy_msg(df, 'donnee2', path, 100, N_round = 3)
   780         df3 = sawtooth_curve(df, 'ect', path, 100, N_round = 1)
  
   ```
   
   
   
   
         
     
         
