from collections import namedtuple
from bs4 import BeautifulSoup
import requests
from csv import writer



# Car=namedtuple('Whatever','color dah milage')
# mycar=Car('red',4000, 3)
# print(mycar.milage)

response = requests.get("https://alternative.me/crypto/fear-and-greed-index/")



soup=BeautifulSoup(response.text,'html.parser')

circles = soup.find_all(class_="fng-value")
ratings={}
for post in circles:
	dic={}
	rating=post.find(class_="fng-circle").get_text()
	dic.update({'Rating':rating})
	time=post.find(class_="gray").get_text()
	status=post.find(class_="status").get_text()
	dic.update({'Status':status})
	ratings.update({time:dic})
	print(f'{time}: {status} ({rating})')
