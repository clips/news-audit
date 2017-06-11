from bs4 import BeautifulSoup as BS
import requests
import urllib


def extract_photoshopped_images(comment_link, count):
  r = requests.get(comment_link).text
  soup = BS(r, 'html.parser')

  entries = soup.find_all('div', class_='md')

  for entry in entries:
    try:
      interest = entry.find('a').get('href')
      if interest:
        interest_pic = str(interest).find('jpg')  
        if interest_pic != -1:
          print(str(interest), count)
    except:
      pass



def find_pictures():
  r = requests.get('https://www.reddit.com/r/photoshopbattles/').text
  soup = BS(r, 'html.parser')
  entries = soup.find_all('div', class_='entry')
  count = 0

  for entry in entries:
    temp = entry.find_all('p', class_='title')
    
    if temp[0].find('span', title='Battle') or str(temp[0].text).find('Photoshops Only') != -1:
      link_class = temp[0].find_all('a')
      
      # print(link_class)
      # image_link = link_class[0].get('data-href-url')
      # if image_link:
      #   # Save the actual picture
      #   fn = str(count) + '.jpg'
      #   urllib.urlretrieve(image_link, fn)

      comment_link = entry.find('ul', class_='flat-list buttons').find('li', class_='first').find('a').get('data-href-url')
      comment_link = 'https://reddit.com' + comment_link

      extract_photoshopped_images(comment_link, count)

      count += 1


if __name__ == '__main__':
  find_pictures()
