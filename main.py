# Requires Python 3.5 or higher;

# Import libraries
import platform
from tempfile import TemporaryDirectory
from pathlib import Path
from fileinput import filename
import re
import csv
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import os, os.path
import pandas
import cv2
import base64
import numpy as np
from flask import *  
app = Flask(__name__)  

out_directory = Path("~").expanduser()

# Store all the pages of the PDF in a variable
const_file_list = []
image_file_list = []

# storing data page wise
page_data =[]


text_file = out_directory / Path("c_text.txt")

app = Flask(__name__)  
  
@app.route('/')  
def main():  
    return render_template("index.html")  
  
@app.route('/success', methods = ['POST'])  
def success():
    ''' Main execution point of the program'''
    f = request.files['file'].read()
    pdf_data = []
    with TemporaryDirectory() as tempdir:
        pdf_pages = convert_from_bytes(f, 500)
        for page_enumeration, page in enumerate(pdf_pages, start=1):
            print(page_enumeration)
            if (page_enumeration == 1 or page_enumeration == 2 or page_enumeration == len(pdf_pages)):
                name = f"{tempdir}\page_{page_enumeration:03}.jpg"
                page.save(name, "JPEG")
                const_file_list.append(name)
            else:
                name = f"{tempdir}\page_{page_enumeration:03}.jpg"
                page.save(name, "JPEG")
                image_file_list.append(name)
        with open(text_file, "a") as output_file:
            for i, image_file in enumerate(image_file_list):
              image = cv2.imread(image_file)
              original = image.copy()
              gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
              thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,51,9)
              cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
              cnts = cnts[0] if len(cnts) == 2 else cnts[1]
              for c in cnts:
                  cv2.drawContours(thresh, [c], -1, (255,255,255), -1)

              kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
              opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=4)

              cnts = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
              cnts = cnts[0] if len(cnts) == 2 else cnts[1]
              area_treshold = 4000
              image_number = 0
              for c in cnts:
                  if cv2.contourArea(c) > area_treshold :
                    x,y,w,h = cv2.boundingRect(c)
                    cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 3)
                    ROI = original[y:y+h, x:x+w]
                    imgheight=ROI.shape[0]
                    imgwidth=ROI.shape[1]
                    cv2.imwrite("save/ROI_{}.png".format(image_number), ROI)
                    image_number += 1
              path = "save"
              valid_images = [".jpg",".gif",".png",".tga"]
              directory_number = 0
              for images in os.listdir(path):
                  if (images.endswith(".png")):
                      directory_number += 1
                      print(images, directory_number)
                      file_path = os.path.join(path, images)
                      img = cv2.imread(file_path)
                      image_copy = img.copy()
                      imgheight=image_copy.shape[0]
                      imgwidth=image_copy.shape[1]
                      if (imgwidth > 1260):
                        if( imgwidth > 2522):
                            M = imgheight
                            N = imgwidth//3
                            for y in range(0,imgheight,M):
                                for x in range(0, imgwidth, N):
                                    y1 = y + M
                                    x1 = x + N
                                    tiles = image_copy[y:y+M,x:x+N]
                                    if (tiles.shape[1] > 12):
                                        cv2.rectangle(image_copy, (x, y), (x1, y1), (0, 255, 0))
                                        cv2.imwrite("patched/" + str(x + directory_number) + '_' + str(y + directory_number)+".jpg",tiles)
                            try:
                                if os.path.isfile(file_path) or os.path.islink(file_path):
                                    os.unlink(file_path)
                                elif os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                            except Exception as e:
                                print('Failed to delete %s. Reason: %s' % (file_path, e))
                        else:
                            M = imgheight
                            N = imgwidth//2
                            for y in range(0,imgheight,M):
                                for x in range(0, imgwidth, N):
                                    y1 = y + M
                                    x1 = x + N
                                    tiles = image_copy[y:y+M,x:x+N]
                                    if (tiles.shape[1] > 12):
                                        cv2.rectangle(image_copy, (x, y), (x1, y1), (0, 255, 0))
                                        cv2.imwrite("patched/" + str(x + directory_number) + '_' + str(y + directory_number)+".jpg",tiles)
                            try:
                                if os.path.isfile(file_path) or os.path.islink(file_path):
                                    os.unlink(file_path)
                                elif os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                            except Exception as e:
                                print('Failed to delete %s. Reason: %s' % (file_path, e))
                      else:
                           cv2.imwrite("patched/" + str(directory_number) + 'hello_' +str(directory_number) +".jpg",image_copy)
                           try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                           except Exception as e:
                                print('Failed to delete %s. Reason: %s' % (file_path, e))
              folder = 'patched'
              for filename in os.listdir(folder):
                  file_path = os.path.join(folder, filename)
                  text = str(((pytesseract.image_to_string(Image.open(file_path)))))
                  data = {}
                  text = re.sub("\n", " ", text)
                  code = re.match(r"(?<![^\s,])[A-Z]+[0-9]+(?![^\s,])", text)
                  if code:
                      data['Voter-Id'] = code.group()
                  else:
                      data['Voter-Id'] = text[0:10]
                  text = text.replace("Father's Name", "\nFather").replace("Mother's Name", "\nFather").replace("Husband's Name", "\nFather").replace("Other's Name", "\nFather").replace("House Number", "\nHouse").replace("Age", "\nAge").replace("Gender", "\nGender").replace("Photo", "\nPhoto").replace("Available", "\nAvailable").replace("Name", "\ntitle")
                  name = re.findall("title(.*)\n", text)
                  if len(name) > 0:
                      data['Name'] = name[0].replace(":","").replace("-","").replace("=","").lstrip().strip()
                  else:
                      data['Name'] = 'None'
                  guardian = re.findall("Father(.*)\n", text)
                  if len(guardian) > 0:
                      data['Guardian'] = guardian[0].replace(":","").replace("-","").replace("=","").lstrip().strip()
                  else:
                      data['Guardian'] = 'None'
                  age = re.findall("Age(.*)\n", text)
                  if len(age) > 0:
                      data['Age'] = age[0].replace(":","").replace("-","").replace("=","").lstrip().strip()
                  else:
                      data['Age'] = 'None'
                  gender = re.findall("Gender(.*)\n", text)
                  if len(gender) > 0:
                      data['Gender'] = gender[0].replace(":","").replace("-","").replace("=","").lstrip().strip()
                  else:
                      retry = re.findall("Gender(.*)", text)
                      if len(retry) > 0:
                          data['Gender'] = retry[0].replace(":","").replace("-","").replace("=","").lstrip().strip()
                      else:
                          data['Gender']= 'None'
                  house = re.findall("House(.*)\n", text)
                  if len(house) > 0:
                      data['House-No'] = house[0].replace(":","").lstrip().strip()
                  else:
                      data['House-No'] = 'None'
                  pdf_data.append(data)
                  try:
                      if os.path.isfile(file_path) or os.path.islink(file_path):
                          os.unlink(file_path)
                      elif os.path.isdir(file_path):
                          shutil.rmtree(file_path)
                  except Exception as e:
                      print('Failed to delete %s. Reason: %s' % (file_path, e))
              data = {'code': "NEXT PAGE :----",'Voter-Id': "", 'Name': "", 'Guardian': "", 'Age': "", 'Gender': "", 'House-No': ""}
              pdf_data.append(data)
            data_file = open('data_file.csv', 'w')
            csv_writer = csv.writer(data_file)
            count = 0
            for page in pdf_data:
                if count == 0:
                    header = page.keys()
                    csv_writer.writerow(header)
                    count += 1
                csv_writer.writerow(page.values())
            data_file.close()        
            return render_template("success.html", data = pdf_data)              
if __name__ == "__main__":
   app.run()
