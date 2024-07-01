from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# Configuration du service pour le driver Chrome
service = Service(ChromeDriverManager().install())

# Initialisation du driver sans utiliser 'executable_path'
driver = webdriver.Chrome(service=service)

# URL de la page à scraper
url = 'https://www.lemonde.fr/les-decodeurs/article/2024/07/01/la-carte-des-resultats-des-legislatives-au-premier-tour-et-le-tableau-des-candidats-qualifies_6245574_4355771.html'

# Ouvrir la page
driver.get(url)

# Attendre que le tableau soit chargé (ajustez le sélecteur selon votre cas)
driver.implicitly_wait(10)  # Temps d'attente implicite

# Trouver le tableau (ajustez le sélecteur selon votre cas)
table = driver.find_element(By.XPATH, '//*[@id="d_desist"]')  # Utilisez le bon sélecteur

# Extraire le HTML du tableau
table_html = table.get_attribute('outerHTML')

# Fermer le driver
driver.quit()

with open("out.html", "w") as f:
    f.write(table_html)

from bs4 import BeautifulSoup

# Lire le fichier HTML
with open('out.html', 'r', encoding='utf-8') as file:
    content = file.read()

# Parser le contenu HTML avec BeautifulSoup
soup = BeautifulSoup(content, 'lxml')

# Initialiser la liste des candidats
candidats_ensemble = []

# Trouver tous les divs avec la classe "tableauLigne interactive clair"
table_rows_clair = soup.find_all('div', class_='tableauLigne interactive fonce')
table_rows_fonce = soup.find_all('div', class_='tableauLigne interactive fonce')

table_rows = table_rows_clair + table_rows_fonce

for row in table_rows:
    # Extraire les informations de la circonscription
    dept_cell = row.find('div', class_='tableauCellule dept')
    circo_nom = dept_cell.find_all('div', class_='circo')[0].text.strip()
    circo_num = dept_cell.find_all('div', class_='circo')[1].text.strip()
    circo = f"{circo_nom} - {circo_num}"

    # Trouver la cellule des partis
    partie_cell = row.find('div', class_='tableauCellule parti')
    parties = partie_cell.find_all('div', class_='famille')
    
    # Trouver la cellule des noms
    nom_cell = row.find('div', class_='tableauCellule flex nom')
    candidats = nom_cell.find_all('div', class_='candidat')

    # Parcourir les partis et les candidats en parallèle
    for i in range(min(len(parties), len(candidats))):
        parti = parties[i].text.strip()
        candidat_div = candidats[i]
        candidat_nom = candidat_div.text.strip()
        
        # Vérifier si l'étiquette contient "ENSEMBLE"
        if "ensemble" in parti.lower():
            # Vérifier s'il y a une mention de désistement
            desistement = bool(candidat_div.find('span', class_='carre desistement'))
            
            # Ajouter le candidat à la liste
            candidats_ensemble.append({
                'nom': candidat_nom,
                'desistement': desistement,
                'circo': circo[:-6].strip(),
                "parti": parti
            })

# Calculer le nombre total de candidats "ENSEMBLE"
total_candidats = len(candidats_ensemble)

# Calculer le nombre de désistements parmi les candidats "ENSEMBLE"
desistements = sum(1 for candidat in candidats_ensemble if candidat['desistement'])

# Calculer le pourcentage de désistements
pourcentage_desistements = (desistements / total_candidats) * 100 if total_candidats > 0 else 0

print("Total : " + str(len(candidats_ensemble)))

with open("out.csv", "w") as f:
    for c in candidats_ensemble:
        l = f"{c['circo']}, {c['nom']}, {c['parti']}, {'OUI' if c['desistement'] else 'NON'}"
        f.write(l + "\n")
        print(l)

print("\n")
print(f"Nombre total de candidats ENSEMBLE: {total_candidats}")
print(f"Nombre de désistements: {desistements}")
print(f"Pourcentage de désistements: {pourcentage_desistements:.2f}%")
