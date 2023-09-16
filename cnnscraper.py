import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv
import os

#images directory and csv file
folder_name = "article_images"
csv_file = "data.csv"

if not os.path.exists(folder_name):
    os.makedirs(folder_name)


#URL where we want to fetch news from
url = 'https://edition.cnn.com/'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')


div_content=soup.find_all('div',class_='card container__item container__item--type-section container_lead-plus-headlines__item container_lead-plus-headlines__item--type-section')

#To avoid fetching similar news article links
links=set()

for d in div_content:
    anchor_tags = d.find_all('a')
    for anchor_tag in anchor_tags:
        links.add(anchor_tag['href'])

new_link_list=[]

#handling edge cases where the link is incomplete url we add its prefix edition.cnn.com
for s in links:
    if not s.startswith("https://edition.cnn.com/"):
        updated_string="https://edition.cnn.com"+ s
        new_link_list.append(updated_string)

#available_dates=> storing all the available dates of article to choose from
available_dates=set()
#my_dict=> is a dictionary which maps articles on particular date which we can later use for fetching news
my_dict={}

#get_dates=>finds date when the article was published
def get_dates(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    timestamp_div = soup.find('div', class_='timestamp')
    #regex to extract date
    date_pattern = r'(\w+ \d{1,2}, \d{4})'  
    if timestamp_div:
        date = re.findall(date_pattern, timestamp_div.text)
        available_dates.add(date[0])
        if date[0] not in my_dict:
            my_dict[date[0]] = []  
        my_dict[date[0]].append(url)  

#get_data=> extracts all the required information that is needed to be stored (text and image data)
def get_data(url,writer):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    img_tags = soup.find_all('img')
    h1 = soup.find('h1', class_='headline__text inline-placeholder')
    heading=h1.text

    para=soup.find_all('p', class_='paragraph inline-placeholder')
    ptext=''
    for p in para:
        ptext+=p.text

    for img_tag in img_tags:
        src = img_tag.get('src')
        alt = img_tag.get('alt')
        nh = h1.text
        if src and alt:

            image_name = os.path.basename(src)
            image_name = re.sub(r'[^\w\s.-]', '', image_name) 
            image_name = os.path.splitext(image_name)[0] + '.jpg'
            
            path_image = os.path.join(folder_name, image_name)            
            #downloading images
            # Check if the image file already exists
            if not os.path.exists(path_image):
                response = requests.get(src)
                if response.status_code == 200:
                    with open(path_image, 'wb') as file:
                        file.write(response.content)
                    print(f"Image downloaded and saved to {path_image}")
                else:
                    print(f"Failed to download image. Status code: {response.status_code}")

            writer.writerow({'news_headline' : heading,'news_content': ptext,'img_description' : alt,'img_link':src,'local_path':path_image})

if __name__ == "__main__":
    #getting all the dates of the fetched articles
    for i in new_link_list:
        get_dates(i)

    # sorting the available dates
    available_dates= sorted(available_dates, key=lambda x: datetime.strptime(x, "%B %d, %Y"))

    print("Available Dates:")
    for i, date in enumerate(available_dates, start=1):
        print(f"{i}. {date}")

    #list for storing the selected dates
    selected_list = []
    while True:
        try:
            user_choice = int(input("Choose one date at a time where you want to get news for from the available options(eg 1, 2, 3): "))
            if 1 <= user_choice <= len(available_dates):
                selected_date = available_dates[user_choice - 1]
                selected_list.append(selected_date)
                more_dates = input("Do you want to select more dates? (yes/no): ").strip().lower()
                if more_dates != "yes":
                    break
            else:
                print("Invalid input. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Open the CSV file for writing
    # Check if the CSV file already exists
    if os.path.exists(csv_file):
        os.remove(csv_file)

    with open(csv_file, mode='w', encoding="utf-8") as file:
        headers = ["news_headline","news_content","img_description", "img_link","local_path"]
        writer = csv.DictWriter(file, delimiter=',', lineterminator='\n',fieldnames=headers)
        writer.writeheader()    

        for i in selected_list:
            for url in my_dict[i]:
                get_data(url,writer)
        
    print("\n<-------Your data.csv has been successfully created and images have been stored under article_images------->")