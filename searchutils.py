import re
import base64
import requests
import time
import random
from random import randrange
from bs4 import BeautifulSoup
import pandas as pd 
import torch 
import torch.nn as nn 
from transformers import *
from utils import *
import json
import psycopg2
import requests
import numpy as np
import threading


def fastsearch(inputtext, listtext):
    # ranks individual ones 
    
    return 1

def deepsearch(inputtext, listtext):
    
    return listtext[0]


def fastdbsearch(inputtext, cur, conn, outputformat=None):
    # outputformat options = "ranking list", "top 1 patent list", 
    
    abstracts = []
    try:
        cur.execute("SELECT id, docnumber, abstract FROM patents")
    except:
        conn.rollback()
    else:
        abstracts = cur.fetchall()
        
    return 1
        


        
    
    

