#!/usr/bin/python3.5

import sys
import os
import time
import inotify.adapters
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import configparser
import logging
import syslog
import logging.handlers
import daemon
import signal

do_exit = False

config = configparser.ConfigParser()

config.read('/home/tcalatayud/sendMailPython/script.ini')

#print(config.sections())

PIDFILE = config['config_daemon']['pidfile']
logfile = config['config_daemon']['logfile']

#mylogging
#logging.basicConfig(filename=logfile,level=logging.INFO)

syslog.openlog("monitor",logoption=syslog.LOG_PID)

def reload_config(signum, stackframe):
    syslog.syslog("caught USR1 signal")

def terminate_daemon(signum, stackframe):
    syslog.syslog("caught TERM signal")

    
def scriptDaemon():
    context = daemon.DaemonContext()
    #logging.info("Deamon created with default context")
    syslog.syslog("Daemon created with default context")
    
    #context.stdout = open('/var/log/MyLog/stdout','w+')
    #context.stderr = open('/var/log/MyLog/stderr','w+')

    context.signal_map = {
        signal.SIGUSR1: reload_config,
        #signal.SIGTERM: terminate_daemon
    }
    
    with context:
        syslog.syslog(syslog.LOG_INFO,"DAEMON STARTED")
         
        i = inotify.adapters.Inotify()      
        
        #i.add_watch(b'/home/tcalatayud/sendMailPython/dossier')
        i.add_watch((config['config_inotify']['watchFolder']).encode('ascii'))
        
        syslog.syslog(syslog.LOG_INFO,"Watch configurated")

        #fromaddr = "t.calatayud@maine-et-loire.fr"
        #toaddr = "t.calatayud@maine-et-loire.fr"

        fromaddr = config['config_mail']['fromaddr']
        toaddr = config['config_mail']['toaddr']
      
        msg = MIMEMultipart()

        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "test"

        body = "Bonjour ceci est un test"

        msg.attach(MIMEText(body, 'plain'))
        
        #logging.info(os.getpid())

        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                if header.mask == 8:
                    fileToSend = str(watch_path)[2:-1]+"/"+str(filename)[2:-1]
                    syslog.syslog(syslog.LOG_INFO,fileToSend)
                    syslog.syslog(syslog.LOG_INFO,str(type_names))
                  
                    fileN = str(filename)[2:-1]

                    attachment = open(fileToSend, "rb")

                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload((attachment).read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', "attachment; filename= %s" % fileN)
         
                    msg.attach(part)
                    
                    server = smtplib.SMTP(config['config_mail']['server'],config['config_mail']['port'])
                    server.starttls()
                    text = msg.as_string()
                    server.sendmail(fromaddr, toaddr, text)

                    syslog.syslog(syslog.LOG_INFO,"send mail")
         
                    server.quit()            


if __name__ ==  "__main__":
    if len(sys.argv) == 2:
        if 'start' ==  sys.argv[1]:
            scriptDaemon()      
        elif 'stop' == sys.argv[1]:
            print('stop')    
        elif 'status' == sys.argv[1]:
            try: 
                pf = open((PIDFILE),'r')
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None
            except SystemExit:
                pid = None

            if pid:
                print("MyScriptDaemon is running as pid %s" % pid) 
            else:
                print("MyScriptDaemon is not running.")
    else:
        print("Unknown command")
        sys.exit(2)
        sys.exit(0)
else:
    print("Usage: %s start|stop|status" % sys.argv[0])
    sys.exit(2)

# vim: ts=4 sw=4 sts=4 expandtab
