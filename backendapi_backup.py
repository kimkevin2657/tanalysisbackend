# -*- coding: utf-8 -*- 


from flask import Flask, request
from flask_cors import CORS, cross_origin
import json
import psycopg2
import requests
import base64
from time import gmtime, strftime
import datetime
import time
import pytz
import urllib

from PIL import Image
import io
import cv2
import numpy as np
import imutils


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display

from bs4 import BeautifulSoup
import csv

import re

import pandas as pd 
import torch 
import torch.nn as nn 
from transformers import * # pip install transformers==4.3.3
#from googletrans import Translator # pip install googletrans==4.0.0-rc1  
from keybert import KeyBERT # pip install keybert 

#from summarizer import Summarizer   # pip install bert-extractive-summarizer

from utils import *


PORT = 3030

cors = CORS()

app = Flask(__name__)

CORS(app)

cors.init_app(app)


DB_NAME = "uspatent"
DB_USER = "uspatent"
DB_PASS = "uspatentUSPATENT"
DB_HOST = "uspatent.cptpezist902.ap-northeast-2.rds.amazonaws.com"
DB_PORT = "5432" 
conn = psycopg2.connect(database=DB_NAME,user=DB_USER,password=DB_PASS,host=DB_HOST,port=DB_PORT)
cur = conn.cursor()



def currenttime():
    tz1 = pytz.timezone("UTC")
    tz2 = pytz.timezone("Asia/Seoul")
    dt = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    dt = datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M:%S")
    dt = tz1.localize(dt)
    dt = dt.astimezone(tz2)
    dt = dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


def relaxed_decode_base64(data):
    data2 = urllib.parse.unquote(urllib.parse.unquote(data))
    for i in range(0,1000):
        if len(data2) % 4 == 0:
            if i == 0:
                print(" no padding needed ")
            print(i)
            break
        else:
            data2 += "="

    return base64.urlsafe_b64decode(data2)


##
### mac 
##
# brew install geckodriver
# which geckodriver
#driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver')



##
### ubuntu GUI-less
##
#display = Display(visible=0, size=(1920, 1080))
#display.start()

#from webdriver_manager.chrome import ChromeDriverManager
#path = '/home/ubuntu/chromedriver'
#driver = webdriver.Chrome(path)


##
### windows GUI
##
#options = Options()
#options.add_argument("--headless")
#options.binary_location = r'C:\\Program Files\\Mozilla Firefox\\firefox.exe'
#driver = webdriver.Firefox(executable_path=r"C:\\Users\\Gravitera\Downloads\\geckodriver-v0.30.0-win64\\geckodriver.exe")


kw_model = KeyBERT()
#model = Summarizer()


@app.route("/patentnumbersearch", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def patentnumbersearch():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        
        #print(" ==== successful display start    ", display)

        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

        patentnumber2 = data["Keyword"]
        patentnumber = "".join("".join("".join(patentnumber2.split(":")).split("/")).split(","))
        
        url = getPatentUrl(patentnumber, driver, By, Keys)
        
        """
        appnumber = getPatentnumberFromUrl(url)
        if appnumber[0][:2].lower() != "us":
            f = open('timesleep.json')
            data = json.load(f)
            seconds = data["timesleep"]
            if seconds > 0:
                time.sleep(seconds + randrange(0, 150))
            f.close()
            return json.dumps({"Result": []}), 200, {'ContentType':'application/json'}
        """
        
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        
        description = getDescription(soup)
        abstract = getAbstract(soup)
        claims = getClaims(soup)
        title = getTitle(soup)
        
        keywords = kw_model.extract_keywords(abstract + description, 
                                    keyphrase_ngram_range = (1,1), 
                                    top_n = 10) 
        
        blocks = getBlocks(abstract, description, keywords[0][0])
        
        imgs = getImages(soup)
        imgslist = []
        for i in range(0, len(imgs)):
            imgslist.append({"content": imgs[i]})
        
        
        Specification = {
            "name": "명세서",
            "content": [
                {
                    "title": "Title",
                    "subject": title,
                },
                {
                    "title": "Abstract",
                    "subject": abstract,
                },
                {
                    "title": "Description",
                    "subject": description,
                }
            ],
            "scroll": 0
        }
        
        Summary = {
            "name": "요약",
            "content": abstract,
            "scroll": 0
        }
        Block = {
            "name": "발췌",
            "content": blocks,
            "scroll": 0
        }
        Image = {
            "name": "도면",
            "content": imgslist,
            "scroll": 0
        }
        
        
        Resultdict = {
            "Result": [
                Specification,
                Summary,
                Block,
                Image
            ]
        }
        
        driver.quit()
        

        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()

        
        return json.dumps(Resultdict), 200, {'ContentType':'application/json'}
        
        
@app.route("/targetpatentnumbersearch", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def targetpatentnumbersearch():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)

        patentnumber2 = data["Keyword"]
        patentnumber = "".join("".join("".join(patentnumber2.split(":")).split("/")).split(","))
        
        
        url = getPatentUrl(patentnumber, driver, By, Keys)
        
        """
        appnumber = getPatentnumberFromUrl(url)
        if appnumber[0][:2].lower() != "us":
            f = open('timesleep.json')
            data = json.load(f)
            seconds = data["timesleep"]
            if seconds > 0:
                time.sleep(seconds + randrange(0, 150))
            f.close()
            return json.dumps({"Result": []}), 200, {'ContentType':'application/json'}
        """
        
        soup = BeautifulSoup(requests.get(url).text, "html.parser")

        focus = getFocus(kw_model, getAbstract(soup), getDescription(soup))
        
        claims = getClaims(soup)
        
        description = getDescription(soup)
        abstract = getAbstract(soup)
        claims = getClaims(soup)
        title = getTitle(soup)
        
        Specification = {
            "name": "명세서",
            "content": [
                {
                    "title": "Title",
                    "subject": title,
                },
                {
                    "title": "Abstract",
                    "subject": abstract,
                },
                {
                    "title": "Description",
                    "subject": description,
                }
            ],
            "scroll": 0
        }
        
        resultdict = {
            "Result": {
                "priorLiterature": getPatentnumberFromUrl(url)[1],
                "claim": [{"id": 0, "addClaim": claims}],
                "focus": focus,
                "Specification": Specification
            }
        }
        
        
        #time.sleep(300 + randrange(50, 150))    
    
   #     time.sleep(10)
        driver.quit()
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()
        
        return json.dumps(resultdict), 200, {'ContentType':'application/json'}
        
        



@app.route("/targetpatenttextsearch", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def targetpatenttextsearch():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)


        typeval = data["type"]
        technologylist = data["technologyList"]
        compositionList = data["compositionList"]
        searchText = data["searchText"]
        
        grandsearchtext = ""
        
        if len(technologylist) != 0:
            for q in range(0, len(technologylist)):
                grandsearchtext += technologylist[q]
                grandsearchtext += " "
        
        if len(compositionList) != 0:
            for q in range(0, len(compositionList)):
                grandsearchtext += compositionList[q]
                grandsearchtext += " "

        grandsearchtext += searchText
        
        links = getGoogleTextSearch(grandsearchtext)
        
        soup = BeautifulSoup(requests.get(links[0]).text, "html.parser")
        
        claims = getClaims(soup)
        focus = getFocus(kw_model, getAbstract(soup), getDescription(soup))
        
        claimslist = [{"id": 0, "addClaim": claims}]
        
        description = getDescription(soup)
        abstract = getAbstract(soup)
        claims = getClaims(soup)
        title = getTitle(soup)
        
        Specification = {
            "name": "명세서",
            "content": [
                {
                    "title": "Title",
                    "subject": title,
                },
                {
                    "title": "Abstract",
                    "subject": abstract,
                },
                {
                    "title": "Description",
                    "subject": description,
                }
            ],
            "scroll": 0
        }
        
        resultdict = {
            "Result": {
                "priorLiterature": getPatentnumberFromUrl(links[0])[1], 
                "claim": claimslist,
                "focus": focus,
                "Specification": Specification
            }    
        }
        
        for i in range(0, 5):
        
            f = open('timesleep.json')
            data = json.load(f)
            seconds = data["timesleep"]
            if seconds > 0:
                time.sleep(seconds + randrange(0, 150))
            f.close()
        

        return json.dumps(resultdict), 200, {'ContentType':'application/json'}


@app.route("/targetpatentdetailsearch", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def targetpatentdetailsearch():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
        
        
        inputpriorLiterature = data["patentid"]
        
        technologyList = data["technologyList"]
        compositionList = data["compositionList"]
        searchText = data["searchText"]
        claim = data["claim"]
        
        dateType = data["dateType"]
        startDate = data["startDate"]
        endDate = data["endDate"]
        inventor = data["inventer"]
        assignee = data["assignee"]
        
        links = []
        
        for i in range(0, len(technologyList)):
            links += getGoogleTextSearch(technologyList[i]["content"])
        for i in range(0, len(compositionList)):
            links += getGoogleTextSearch(compositionList[i]["content"])
        links += getGoogleTextSearch(searchText)
        for i in range(0, len(claim)):
            for j in range(0, len(claim[i]["addClaim"])):
                links += getGoogleTextSearch(claim[i]["addClaim"][j])
                
        print(" =========== raw links  ========  ")
        for i in range(0, len(links)):
            print(links[i])
                
        date_format = "%Y-%m-%d"
    
        
        filtered_dates = []
        if startDate != "":
            startdate = datetime.datetime.strptime(startDate, date_format)
            enddate = datetime.datetime.strptime(endDate, date_format)
            for i in range(0, len(links)):
                soup = BeautifulSoup(requests.get(links[i]).text, "html.parser")
                dateval = getDate(soup)
                a = datetime.datetime.strptime(dateval, date_format)
                if startdate <= a <= enddate:
                    filtered_dates.append(links[i])
        if inventor != "":
            for i in range(0, len(links)):
                soup = BeautifulSoup(requests.get(links[i]).text, "html.parser")
                inventorval = getInventor(soup)
                for q in range(0, len(inventorval)):
                    if inventor == inventorval[q]:
                        filtered_dates.append(links[i])
        if assignee != "":
            for i in range(0, len(links)):
                soup = BeautifulSoup(requests.get(links[i]).text, "html.parser")
                assigneeval = getAssignee(soup)
                if assignee == assigneeval:
                    filtered_dates.append(links[i])    
                    
        print(" ==================== filtered dates, inventor, assignee ==========  ")
        for i in range(0, len(filtered_dates)):
            print(filtered_dates)
                    
                    
        ###
        ###     SHOULD FILTER OUT BASED ON QUERY LISTS RATHER THAN APPENDING
        ###
                    
        patents = []
        for i in range(0, len(links)):
            soup = BeautifulSoup(requests.get(links[i]).text, "html.parser")
            patents.append(converttotuple(soup))
            
            
        MainPannel = []
        for i in range(0, len(patents)):
            tempdict = dict()
            tempdict["priorLiterature"] = patents[i][0]
            tempdict["ranking"] = i+1
            if len(data["focus"]) != 0:
                tempdict["keyword"] = getKeyword(patents[i][6], patents[i][7], data["focus"])
            else:
                tempdict["keyword"] = []
            MainPannel.append(tempdict)
            
            
        
        soup = BeautifulSoup(requests.get(getPatentUrl(inputpriorLiterature, driver, By, Keys)).text, "html.parser")
        abstract = getAbstract(soup)
        imglinks = getImagesLinks(soup)
        title = getTitle(soup)
        abstract = getAbstract(soup)
        description = getDescription(soup)
        
            
            
        Summary = [abstract]
        Drawing = []
        for i in range(0, len(imglinks)):
            temp64 = ""
            try:
                temp64 = base64.b64encode(requests.get(imglinks[i]).content).decode("utf-8")  
            except:
                pass
            if temp64 != "":
                Drawing.append(temp64)
        Specification = [
            {
                "title": "Title",
                "content": title
            },
            {
                "title": "Abstract",
                "content": abstract
            },
            {
                "title": "Description",
                "content": description
            }
        ]
        
        Result = {
            "patentid": inputpriorLiterature,
            "MainPannel": MainPannel,
            "Summary": Summary,
            "Drawing": Drawing,
            "Specification": Specification
        }
        
        
        
        driver.quit()
        
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        print(" sleep seconds    ", seconds)
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        print(" sleep seconds    ", seconds)
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()
        

        return json.dumps(Result), 200, {'ContentType':'application/json'}
        






@app.route("/newfocusword", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def newfocusword():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
        
        patentid2 = data["patentid"]
        patentid = "".join("".join("".join(patentid2.split(":")).split("/")).split(","))
        keywords = data["keyword"]["new"]
        
        url = getPatentUrl(patentid, driver, By, Keys)
        
        soup = BeautifulSoup(requests.get(url).text, "html.parser")
        
        abstract = getAbstract(soup)
        
        description = getDescription(soup)
        
        Focus = getFocus(kw_model, abstract, description, inputkeywords=keywords)
        
        resultdict = {
            "focus": Focus
        }
        
        #time.sleep(300 + randrange(50, 150))    
        
  #      time.sleep(10)
        driver.quit()
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()

        return json.dumps(resultdict), 200, {'ContentType':'application/json'}
     
     
     
@app.route("/mainpanelclick", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def mainpanelclick():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
        
        patentid2 = data["patentid"]
        patentid = "".join("".join("".join(patentid2.split(":")).split("/")).split(","))
        
        priorLiterature2 = data["priorLiterature"]
        inputpriorLiterature = "".join("".join("".join(priorLiterature2.split(":")).split("/")).split(","))
        
        
        soup = BeautifulSoup(requests.get(getPatentUrl(inputpriorLiterature, driver, By, Keys)).text, "html.parser")
        abstract = getAbstract(soup)
        imglinks = getImagesLinks(soup)
        title = getTitle(soup)
        abstract = getAbstract(soup)
        description = getDescription(soup)
        
            
            
        Summary = [abstract]
        Drawing = []
        for i in range(0, len(imglinks)):
            temp64 = ""
            try:
                temp64 = base64.b64encode(requests.get(imglinks[i]).content).decode("utf-8")  
            except:
                pass
            if temp64 != "":
                Drawing.append(temp64)
        Specification = [
            {
                "title": "Title",
                "content": title
            },
            {
                "title": "Abstract",
                "content": abstract
            },
            {
                "title": "Description",
                "content": description
            }
        ]
        
        Result = {
            "Summary": Summary,
            "Drawing": Drawing,
            "Specification": Specification
        }
        

        
        
        #       time.sleep(10)
        driver.quit()
        
        """
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()
        """

        return json.dumps({"Result": Result}), 200, {'ContentType':'application/json'}
     
     
@app.route("/detailmappingclick", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def detailmappingclick():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
        
        patent2 = data["patent"]
        patent = "".join("".join("".join(patent2.split(":")).split("/")).split(","))
        priorLiterature2 = data["priorLiterature"]
        priorLiterature = "".join("".join("".join(priorLiterature2.split(":")).split("/")).split(","))
        patentKeyword = data["patentKeyword"]
        
        soup = BeautifulSoup(requests.get(getPatentUrl(patent, driver, By, Keys)).text, "html.parser")
        
        focus = getFocus(kw_model, getAbstract(soup), getDescription(soup), inputkeywords=[patentKeyword])
        
        resultdict = {
            "Extract": [
                {
                    "statements": focus[0]["content"],
                    "Focus": focus
                }
            ]
        }
    
        
        #time.sleep(300 + randrange(50, 150))    
        
 #       time.sleep(10)
        driver.quit()
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()

        return json.dumps(resultdict), 200, {'ContentType':'application/json'}

    
     
@app.route("/detailmappingdrag", methods=["GET", "POST"])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def detailmappingdrag():
    if request.method == "POST":
        data = dict()
        try:
            data = request.get_json()
        except Exception as ex:
            print(ex)
            
        
        #display = Display(visible=0, size=(1920, 1080))
        #display.start()
        option = webdriver.ChromeOptions()
        option.add_argument('headless')

        drivertime = time.time()
        from webdriver_manager.chrome import ChromeDriverManager
        path = '/home/ubuntu/chromedriver'
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option) 
        
        print(" data    ", data)
    
        priorLiterature2 = data["priorLiterature"]
        priorLiterature = "".join("".join("".join(priorLiterature2.split(":")).split("/")).split(","))
        patentKeyword = data["keyword"]
        

        soup = BeautifulSoup(requests.get(getPatentUrl(priorLiterature, driver, By ,Keys)).text, "html.parser")
        
        focus = getFocus(kw_model, getAbstract(soup), getDescription(soup), inputkeywords=[patentKeyword])
        
        resultdict = {
            "Extract": [
                {
                    "statements": focus[0]["content"],
                    "Focus": focus
                }
            ]
        }
        
        #time.sleep(300 + randrange(50, 150))    
        
#        time.sleep(10)
        driver.quit()
        
        f = open('timesleep.json')
        data = json.load(f)
        seconds = data["timesleep"]
        if seconds > 0:
            time.sleep(seconds + randrange(0, 150))
        f.close()
        
        return json.dumps(resultdict), 200, {'ContentType':'application/json'} 
    
    
    
    
@app.route('/timesleep', methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def timesleep():
    if request.method == "GET":
        inputbool = True
        try:
            inputbool = request.args.get("option")
        except:
            pass
        try:
            inputbool = request.get_json()["option"]
        except:
            pass
        inputbool = inputbool.lower()
        if inputbool == "true":
            with open('timesleep.json', 'w', encoding='utf-8') as f:
                json.dump({"timesleep": 300}, f, ensure_ascii=False, indent=4)
        else:
            with open('timesleep.json', 'w', encoding='utf-8') as f:
                json.dump({"timesleep": 0}, f, ensure_ascii=False, indent=4)
        
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

    """
    if request.method == "POST":
        data = request.get_json()
        inputbool = data["option"]
        inputbool = inputbool.lower()
        if inputbool == "true":
            with open('timesleep.json', 'w', encoding='utf-8') as f:
                json.dump({"timesleep": 300}, f, ensure_ascii=False, indent=4) 
        else:
            with open('timesleep.json', 'w', encoding='utf-8') as f:
                json.dump({"timesleep": 0}, f, ensure_ascii=False, indent=4)
            
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    """
    


@app.route('/healthcheck', methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content- Type','Authorization'])
def healthcheck():
    if request.method == "GET":
        
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

    if request.method == "POST":
            
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}






if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(host='0.0.0.0', port=PORT, debug=True)



