import re
import base64
import requests
import time
import random
from random import randrange
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display

def getDescription(soup):
    descriptions = soup.findAll("div", {"class": "description-line"})
    description = descriptions[0].get_text()
    return description

def getAbstract(soup):
    abstract2 = soup.findAll("meta", {"name": "DC.description"})
    abstract = abstract2[0]["content"]
    return abstract

def getClaims(soup):
    dependent_claims2 = soup.findAll("div", {"class": "claim-dependent"})
    dependent_claims = []
    for item in dependent_claims2:
        dependent_claims.append(" ".join(re.sub(' +', ' ',item.get_text()).split()))
    all_claims2 = soup.findAll("div", {"class": "claim-text"})
    all_claims = []
    for item in all_claims2:
        tempbool = False
        currclaim = " ".join(re.sub(' +', ' ',item.get_text()).split())
        for tempitem in dependent_claims:
            if currclaim == tempitem:
                tempbool = True
        if tempbool:
            continue
        all_claims.append(" ".join(re.sub(' +', ' ',item.get_text()).split()))
    return all_claims, dependent_claims    
        

def getTitle(soup):
    title2 = soup.findAll("meta", {"name": "DC.title"})
    title = title2[0]["content"]
    return title


def getFocus(kw_model, abstract, description):
    
    """
    focus: [
      {
        word: '',
        location: [0.56, 0.4, 0.9],
        weight: '',
        frequency: '',
        significance: '',
        content: ['', '', ''],
      },
    ]
    """
    keywords = kw_model.extract_keywords(abstract + description, 
                                    keyphrase_ngram_range = (1,1), 
                                    top_n = 10)
    wholeblock = abstract + description
    wholeblock = wholeblock.split(" ")
    wordcount = len(wholeblock)
    Focus = []
    for i in range(0, len(keywords)):
        tempdict = dict()
        tempdict["word"] = keywords[i][0]
        templocation = []
        tempfreq = 0
        for q in range(0, len(wholeblock)):
            if wholeblock[q] == keywords[i][0]:
                templocation.append(float(q)/float(wordcount))
                tempfreq += 1
        tempdict["location"] = templocation
        tempdict["frequency"] = tempfreq
        tempweight = 0
        score = 0.0
        try:
            score = float(keywords[i][1])
        except:
            pass
            
        if score < 0.33:
            tempweight = 0
        if score >= 0.33 and score < 0.66:
            tempweight = 1
        if score >= 0.66:
            tempweight = 2
        tempdict["weight"] = tempweight
        tempdict["significance"] = keywords[i][0]
        tempdict["content"] = getBlocks(abstract, description, keywords[i][0])
        Focus.append(tempdict)
    return Focus

def getKeyword(abstract, description, inputkeywords):
    
    wholeblock = abstract + description
    wholeblock = wholeblock.split(" ")
    keywords = []
    for i in range(0, len(inputkeywords)):
        freq = 0
        location = []
        for q in range(0, len(wholeblock)):
            if wholeblock[q] == inputkeywords[i]["word"]:
                freq += 1
                location.append(float(q)/float(len(wholeblock)))
        tempdict = dict()
        tempdict["keyword"] = inputkeywords[i]["word"]
        tempdict["frequency"] = freq
        tempdict["ranking"] = i + 1
        tempdict["location"] = location
        keywords.append(tempdict)
    return keywords
                

def getImages(soup):
    
    imglinks2 = soup.findAll("meta", {"itemprop": "full"})
    imglinks = []
    for item in imglinks2:
        imglinks.append(item["content"])
    imgs = []
    for item in imglinks:
        temp64 = ""
        try:
            temp64 = base64.b64encode(requests.get(item).content).decode("utf-8")  
        except:
            pass
        if temp64 != "":
            imgs.append(temp64)
    return imgs


def getB64Links(links):
    imgs = []
    for item in links:
        temp64 = ""
        try:
            temp64 = base64.b64encode(requests.get(item).content).decode("utf-8")  
        except:
            pass
        if temp64 != "":
            imgs.append(temp64)
    return imgs



def getImagesLinks(soup):
    imglinks2 = soup.findAll("meta", {"itemprop": "full"})
    imglinks = []
    for item in imglinks2:
        imglinks.append(item["content"])
    return imglinks

def getInventor(soup):
    temp = soup.findAll("meta", {"scheme": "inventor"})
    inventors = []
    for item in temp:
        inventors.append(item["content"])
    return inventors
    
def getAssignee(soup):
    temp = soup.findAll("meta", {"scheme": "assignee"})
    assignee = temp[0]["content"]
    return assignee

def getDate(soup):
    temp = soup.findAll("time", {"itemprop": "publicationDate"})
    publicationDate = temp[0]["datetime"]
    return publicationDate

def getDatePriority(soup):
    temp = soup.findAll("time", {"itemprop": "priorityDate"})
    publicationDate = temp[0]["datetime"]
    return publicationDate

def getDateFiling(soup):
    temp = soup.findAll("time", {"itemprop": "filingDate"})
    publicationDate = temp[0]["datetime"]
    return publicationDate
        
        
def getBlocks(abstract, description, keyword):
    wholeblock = abstract + description
    sentences = wholeblock.split(".")
    words = [x.split() for x in sentences]
    
    Statements = []
    for i in range(0, len(words)):
        tempbool = False
        for j in range(0, len(words[i])):
            
            ##### perform similarity score
            
            if words[i][j] == keyword:
                tempbool = True
                
        if not tempbool:
            continue
        else:
            Statements.append(sentences[i])
    return Statements
    

    
    
def getPatentUrl(search, driver, By, Keys, EC=None, WebDriverWait=None):
    driver.get("https://patents.google.com/")
    inputElement = ""
    waitcount = 0
    while inputElement == "":
        try:
            inputElement = driver.find_element(By.ID, "searchInput")
            waitcount += 1
        except Exception as ex:
            pass
        time.sleep(0.05)
        if waitcount > 50:
            break
    if waitcount > 48:
        temp = 1
    inputElement = driver.find_element(By.ID, "searchInput")
    inputElement.send_keys(search)
    inputElement.send_keys(Keys.ENTER)
    waitcount = 0
    while driver.current_url == "https://patents.google.com/":
        time.sleep(0.05)
        waitcount += 1
        if waitcount > 50:
            break
    if waitcount > 48:
        temp = 1
    curr_url = driver.current_url
    return curr_url


def getPatentnumberFromUrl(url):
    temp = url.split("/")
    doc_number = ""
    if temp[0] == "https:":
        doc_number = temp[2]
    else:
        doc_number = temp[1]
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    tempdoc = soup.findAll("meta", {"name": "citation_patent_application_number"})
    app_number = tempdoc[0]["content"]
    appnumber = "".join("".join("".join(app_number.split(":")).split("/")).split(","))
    return doc_number, appnumber
    


def getGoogleTextSearch(search):
    tempsearch = search
    searchterms = tempsearch.split()
    wordcount = len(searchterms)
    links = []
    for i in range(0, 10):
        random.shuffle(searchterms)
        randint = 0
        if wordcount != 0:
            randint = randrange(0, wordcount)
        searchterms2 = searchterms[randint:len(searchterms)]
        "".join(searchterms2)
        searchterms2 += " US patent"
        # Faking real user visit.
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3538.102 Safari/537.36 Edge/18.19582"
        }
        # Search query.
        params = {'q': searchterms2}
        html = requests.get(f'https://www.google.com/search?q=',
                            headers=headers,
                            params=params).text
        soup = BeautifulSoup(html, "html.parser")
        for result in soup.select('.yuRUbf'):
            title = result.select_one('.DKV0Md').text
            link = result.select_one('a')['href']
            if link[:27] == "https://patents.google.com/" or link[:22] == "https://www.google.com":
                if link not in links and link != "https://patents.google.com/" and link != "https://patents.google.com/":
                    links.append(link)
        time.sleep(1 + randrange(0,2))
    return links
    
    
def tuplefromweb(soup):
    
    """
    0 DOCNUMBER VARCHAR(256),
    1 APPNUMBER VARCHAR(256),
    2 PATENTTYPE VARCHAR(256),
    3 ASSIGNEE TEXT,
    4 INVENTOR TEXT [],
    5 TITLE TEXT,
    6 ABSTRACT TEXT,
    7 DESCRIPTION TEXT,
    8 CLAIMS JSONB,
    9 PRIORITYDATE TEXT,
    10 FILINGDATE TEXT,
    11 PUBLICATIONDATE TEXT,
    12  IMAGELINKS TEXT []
    """
    
    
    tempdoc = soup.findAll("meta", {"name": "citation_patent_application_number"})
    
    app_number = tempdoc[0]["content"]
    
    appnumber = "".join("".join("".join(app_number.split(":")).split("/")).split(","))
    
    tempdoc = soup.findAll("dd", {"itemprop": "publicationNumber"})
    
    docnumber = tempdoc[0].get_text()
    patenttype = docnumber[len(docnumber)-2:len(docnumber)]
    assignee = getAssignee(soup)
    inventor = getInventor(soup)
    title = getTitle(soup)
    abstract = getAbstract(soup)
    description = getDescription(soup)
    allclaims = getClaims(soup)[0]
    prioritydate = getDatePriority(soup)
    filingdate = getDateFiling(soup)
    publicationdate = getDate(soup)
    imagelinks = getImagesLinks(soup)
    
    
    return [docnumber, appnumber, patenttype, assignee, inventor, title, abstract, description, {"ALL": allclaims}, prioritydate, filingdate, publicationdate, imagelinks]
    
    
    
    
    
