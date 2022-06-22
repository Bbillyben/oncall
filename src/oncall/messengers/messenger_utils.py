import re
from datetime import datetime
from pytz import timezone
import logging

logger = logging.getLogger('smtp_messenger')

def clear_messenger_txt(body):
   
    sep = "</br>"
    # replace new event info in a readable way
    pattern = re.compile(r'(New event info:.*)')
    for evtI in re.findall(pattern, body):
        str = ""
        str+=sep+"New event info:"+sep+"<ul>"
        evtM = evtI.replace("New event info:", "")
        pattern2 = re.compile(r'([\w\d\s]*)\:([\w\d\s]*)')
        for (key, val) in re.findall(pattern2, evtM):
             str+="<li>"+key+" : "+val+"</li>"
        str+="</ul>"
        body = body.replace(evtI, str)
    #change virgule by new line
    #        body = body.replace(",","</br>")

     # replace timestamp
    pattern = re.compile(r'([0-9]{10})')
    for timestamp in re.findall(pattern, body):
            trD = datetime.fromtimestamp(int(timestamp),timezone('Europe/Paris')).strftime('%Y-%m-%d %H:%M')
            body = body.replace(timestamp, trD)

    return body