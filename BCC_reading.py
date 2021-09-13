import os
import ssl
import time
import smtplib
import datetime
import requests
import keyboard
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def file_begin(i):
    logwrite("Beginning csv file", 0)
    csv_files[i].write("Date and time;Total voltage (V);")
    for cell_number in range(1,17):
        text = "Cell "
        text += str(cell_number)
        text += " (V);"
        csv_files[i].write(text)
    csv_files[i].write("Trimmer U_min (V);Trimmer U_max (V);UMINset;UMAXset;Umincell (V);Umaxcell (V);Umincellposition;Umaxcellposition;Udiff (V);lastcellevent;lastcellno;lastellU;lastbattU;connection;relay1;relay2;\n")
    csv_files[i].flush()
    os.fsync(csv_files[i].fileno())

def close_all(count, close_log = True):
    if log_write == True and close_log == True:
        logfile.close()
    for i in range(0, count):
        csv_files[i].close()

def quit():
    keyboard.wait('Enter')
    exit(0)

def error_message(value, onlywrite = 0):
    if onlywrite == 0:
        server = start_email()
    else:
        server = 0
    if server == 0:
        print("Sending emails is not available, check log file for more datails.")
        logmessage = "Sending emails is not available. Informations for sending emails are:\n                               Password: "
        if password == "None" or password == "":
            logmessage += "Password is not set in config file, trying to send emails without STARTTLS and any login request"
        else:
            logmessage += password
        logmessage += "\n                               Sender email: "
        if sender_email == "None" or sender_email == "":
            logmessage += "Sender email is not set in config file so it is impossible to send any email"
        else:
            logmessage += sender_email
        logmessage += "\n                               Receiver email: "
        if receiver_emails[0] == "None" or receiver_emails[0] == "":
            logmessage += "No receiver email adress is set in config file so it is impossible to send any email"
        else:
            for i in range(0,len(receiver_emails)):
                logmessage += receiver_emails[i] + " "
        logmessage += "\n                               SMTP_IP: "
        if SMTP_IP == "None" or SMTP_IP == "":
            logmessage += "SMTP IP is not set in config file so it is impossible to send any email"
        else:
            logmessage += SMTP_IP
        logmessage += "\n                               SMTP_PORT: "
        if SMTP_PORT == "None" or SMTP_PORT == "":
            logmessage += "SMTP PORT is not set in config file so it is impossible to send any email"
        else:
            logmessage += SMTP_PORT
        logmessage += "\n"
        logwrite(logmessage, 2)
        return
    es_date = date_time()
    send_to = ""
    for i in range(len(receiver_emails)):
        send_to += receiver_emails[i] + ", "
    logwrite("Sending error email", 1)
    if value != 9:
        mess = "Error on CPM board with IP: " + IP[all_files]
    else:
        mess = ""
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = send_to
    if value != 9:
        message["Subject"] = subj + " ERROR " + es_date
    else:
        message["Subject"] = subj + " HELLO " + es_date
    if value != 5 and value != 9:
        f_name = csv_files[all_files].name
        csv_files[all_files].close()
        csv_files[all_files] = open(f_name,"rb")
        part = MIMEBase("application", "octet-stream")
        part.set_payload(csv_files[all_files].read())
        encoders.encode_base64(part)
        part.add_header(
        "Content-Disposition",
        f"attachment; filename= {f_name}",
    )
    
    if value == 0:
        mess += ".\nCell number " + str(one_line_values[23]) + " voltage is lower than voltage set on CPM board.\nCell voltage is: " + str(one_line_values[21]) + " Voltage set on CPM board is: " + str(one_line_values[17])
    elif value == 1:
        mess += ".\nCell number " + str(one_line_values[24]) + " voltage is higher than voltage set on CPM board.\nCell voltage is: " + str(one_line_values[22]) + " Voltage set on CPM board is: " + str(one_line_values[18])
    elif value == 2:
        mess += ".\nUdiff is too high: " + str(one_line_values[25]) + "\nMinimum cell voltage is: " + str(one_line_values[21]) + " position: " + str(one_line_values[23]) + "\nMaximum cell voltage is: " + str(one_line_values[22]) + " position: " + str(one_line_values[24])
    elif value == 3:
        mess += ".\nBCC board lost connection to CPM, it cannot read any values."
    elif value == 4:
        mess += ".\nLost connection to BCC with adress: " + IP[all_files] + "\nIf the device will be online again, you will get another email about it."
    elif value == 5:
        mess += ".\nConnection to device with adress: " + IP[all_files] + " is back online."
    elif value == 6:
        mess += ".\nCannot download from any BCC, program is shutting down."
    elif value == 7:
        mess += ".\nCell voltage reached Umin. Actual voltage is: " + str(one_line_values[21]) + "V on position " + str(one_line_values[23]) + "V\nYour minimum voltage in config file is: " + Umin_warning + "\nVoltage set on CPM board is: " + str(one_line_values[17])
    elif value == 8:
        mess += ".\nCell voltage reached Umax. Actual voltage is: " + str(one_line_values[22]) + "V on position " + str(one_line_values[24]) + "V\nYour maximum voltage in config file is: " + Umax_warning + "\nVoltage set on CPM board is: " + str(one_line_values[18])
    elif value == 9:
        mess += "Program for reading values from BCC is starting up"
    message.attach(MIMEText(mess, "plain"))
    if value != 5 and value != 9:
        message.attach(part)
    mess = message.as_string()
    try:
        return_code = server.sendmail(sender_email, receiver_emails, mess)
    except:
        print("An error occured when trying to send email, check your login informations in config file and restart the program")
        error_message(0, 1)
        return
    if value != 5 and value != 9:
        csv_files[all_files].close()
        csv_files[all_files] = open(f_name, "a")
def start_email():
    if send_emails == True:
         try:
            smtp = smtplib.SMTP(SMTP_IP, SMTP_PORT)
            if login == True:
                smtp.starttls(context=context)
                smtp.login(sender_email, password)
         except:
            print("Unable to login to email server, no emails will be sent.\nIf you want to resolve this issue, check your login information in config file")
            logwrite("Unable to login to email server, no emails will be sent", 2)
            return 0
         return smtp
    return 0

def date_time():
    d = str(datetime.datetime.now())
    d = d[:19]
    return d

def logwrite(input, severity, start = 0):
    if log_write == False:
        return
    buffer = ""
    if start == 1:
        buffer += "\n\n"
    buffer += date_time() + " "
    logfile.write(buffer)
    if severity == 0:
        buffer = " [INFO]           "
    elif severity == 1:
        buffer = " [WARNING]        "
    elif severity == 2:
        buffer = " [ERROR]          "
    elif severity == 3:
        buffer = " [CRITICAL ERROR] "
    buffer += input + "\n"
    logfile.write(buffer)
    logfile.flush()
    os.fsync(logfile)

my_file = Path("log.txt")
try:
    if my_file.is_file():
        logfile = open("log.txt", "a")
    else:
        logfile = open("log.txt", "w")
    log_write = True
    logwrite("Program started", 0, 1)
except:
    log_write = False
    print("Failed to open log file, nothing will be written in there...")
    time.sleep(5)
my_file = Path("config.txt")
if my_file.is_file():
    config = open("config.txt","r")
    lines = config.readlines()
    config.close()
    print("Config file loaded")
    logwrite("Config file loaded", 0)
else:
    print("Config file was not found, press Enter to exit")
    logwrite("Config file was not found, program is shutting down", 3)
    quit()
sender_email = "None"
receiver_emails = ["None"]
password = "None"
context = ssl.create_default_context()
period = "None"
IP = ["None"]
File_length = "None"
Udiff_level = "None"
ERROR_interval = "None"
subj = "None"
SMTP_IP = "None"
SMTP_PORT = "None"
Email_name = "None"
Umin_warning = "None"
Umin_warning = "None"
csv_files = []
port = []
send_emails = True
login = False
for line in lines:
    if line[0] == "#":
        continue
    if "IP" in line:
        if line[0] == "S":
            SMTP_IP = line[8:]
            SMTP_IP = SMTP_IP.replace("\n", "")
            continue
        ips = line.split(";")
        IP[0] = ips[0][3:].replace("\n","")
        print("First IP:", IP[0])
        logwrite("First IP: " + IP[0], 0)
        for i in range(1, len(ips)):
            print("Next IP:", ips[i])
            logwrite("Next IP: " + ips[i], 0)
            IP.append(ips[i].replace("\n",""))
    if "PORT" in line:
        if line[0] == "S":
            SMTP_PORT = line[10:]
            SMTP_PORT = SMTP_PORT.replace("\n", "")
            continue
        ports = line.split(";")
        ports[0] = ports[0][5:]
        for i in range(0,len(ports)):
            try:
                port.append(int(ports[i].replace("\n", "")))
            except:
                print("Port: ", ports[i], "is not a valid number, using dafault port 80")
                logwrite("Port: " + str(ports[i]) + " is not a valid number. Using default port 80", 2)
                port.append(80)
    if "Period" in line:
        try:
            period = int(line[7:])
        except:
            print("Period is not a valid number in config file. Using default value 60 seconds.")
            logwrite("Period is not a valid number in config file. Using default value 60 seconds", 2)
            period = 60
            
    if "File_length" in line:
        try:
            File_length = int(line[11:])
        except:
            print("File length is not a valid number in config file. Using default value 1 day.")
            logwrite("File length is not a valid number in config file. Using default value 1 day", 1)
            File_length = 1
    if "Email_send_to" in line:
        emails = line.split(";")
        emails[0] = emails[0][14:]
        First_time = True
        for i in range(0, len(emails)):
            check_buffer = ""
            check_email = False
            for y in (emails[i].replace("\n","")):
                if y == "@" or check_email == True:
                    check_email = True
                    if y == ".":
                        if First_time == True:
                            receiver_emails[0] = emails[i].replace("\n","")
                            First_time = False
                        else:
                            receiver_emails.append(emails[i].replace("\n",""))
                        break
    if "Email_send_from" in line:
        sender_email = line[16:].replace("\n", "")
    if "Email_subject" in line:
        subj = line[14:]
    if "Password" in line:
        password = line[9:].replace("\n", "")
        login = True
    if "Udiff_warning" in line:
        Udiff_level = line[14:]
    if "ERROR_interval" in line:
        ERROR_interval = line[15:]
    if "Email_sender_name" in line:
        Email_name = line[19:]
    if "Umin_warning" in line:
        Umin_warning = line[13:]
    if "Umax_warning" in line:
        Umax_warning = line[13:]
if IP[0] == "None":
    print("IP missing in config file, press Enter to exit")
    logwrite("IP missing in config file, program is shutting down", 3)
    quit()

if period == "None" or period == "\n":
    print("Period is not defined in the config file, using default value 60 seconds")
    logwrite("Period is not defined in the config file, using default value 60 seconds", 1)
    period = 60
if period > 3600:
    print("Period in config file is too high, maximum value is 3600. Using default value 60 seconds")
    logwrite("Period in config file is too high, maximum value is 3600. Using default value 60 seconds", 2)
    period = 60
if File_length == "None" or File_length == "\n":
    print("File length is not defined in the config file, using default value 1 day")
    logwrite("File length is not defined in the config file, using default value 1 day", 1)
    File_length = 1
if receiver_emails[0] == "None":
    print("Receiver email adress is not properly written in config file, no email will be sent.")
    logwrite("Receiver email adress is not properly written in config file, no email will be sent", 1)
    send_emails = False
if (sender_email == "None" or sender_email == "\n" or ("@" not in sender_email or "." not in sender_email)) and send_emails == True:
    print("No sender email found in config file, sending emails is not available")
    logwrite("No sender email found in config file, sending emails in not available", 1)
    send_emails = False
elif (password == "None" or password == "\n") and sender_email == True:
    print("Password to sender email adress is not defined in config file.Program will try to send emails without login command")
    logwrite("Password to sender email adress is not defined in config file. Program will try to send emails without login command")
    login = False

if Udiff_level == "None" or Udiff_level == "\n" or Udiff_level == "0\n":
    print("No emails about Udiff will be sent")
    logwrite("No emails about Udiff will be sent", 1)
    Udiff_level = 0.
try:
    Udiff_level = float(Udiff_level)
    Udiff_level /= 1000
except:
    print("Udiff_warning is not a number, you will not receive any warnings about it.")
    logwrite("Udiff_warning is not a number, you will not receive any warnings about it", 2)
    Udiff_level = 0.
try:
    ERROR_interval = int(ERROR_interval)
except:
    print("ERROR_interval is not properly written in config file, using default value 30 minutes")
    logwrite("ERROR_interval is not properly written in config file, using default value 30 minutes", 2)
    ERROR_interval = 30
try:
    Umin_warning = float(Umin_warning)
    Umin_warning /= 1000.
except:
    print("Umin_warning is not properly written in config file, you will not receive any warnings.")
    logwrite("Umin_warning is not properly written in config file, you will not receive any warnings", 1)
    Umin_warning = 0.
try:
    Umax_warning = float(Umax_warning)
    Umax_warning /= 1000.
except:
    print("Umax_warning is not properly written in config file, you will not receive any warnings.")
    logwrite("Umax_warning is not properly written in config file, you will not receive any warnings", 1)
    Umax_warning = 1000.
if subj == "None" or subj == "\n":
    subj = "BCC"
if len(port) < len(IP):
    print("There are less defined ports than IP adresses, using dafault port 80")
    logwrite("There are less defined ports than IP adresses, using dafault port 80", 1)
    while len(port) != len(IP):
        port.append(80)
if Email_name == "None" or Email_name == "\n":
    print("Using default sender email name (BCC)")
    logwrite("Using default sender email name (BCC)", 1)
    Email_name = "BCC"
my_file = Path("log.txt")
for i in range(0, len(IP)):
    date = str(datetime.datetime.now())
    date = date[:10]
    date += "_" + str(i)
    date += ".csv"
    my_file = Path(date)
    try:
        if my_file.is_file():
            csv_files.append(open(date, "a"))
        else:
            csv_files.append(open(date, "w"))
            file_begin(i)
    except:
        print("Cannot open file:", date, ", maybe it is being used by another program so you need to close it first.\nPress Enter to exit")
        logwrite("Cannot open file:" + date + ", maybe it is being used by another program so you need to close it first", 3)
        quit()
period -= 0.2
devices_offline = []                                                    #Every device have number 0 when it is online or 1 when its connection is lost
URL = []
one_line_values = []                                                    #All values from BCC (one line in table)
daily_limits = [[0 for i in range(7)] for j in range(len(csv_files))]   #0 = min total voltage, 1 = max total voltage, 2 = Ucellmin, 3 = Ucellmax, 4 = Uminposition, 5 = Umaxposition, 6 = maxUdiff
for i in range(0, len(csv_files)):
    URL.append("http://" + str(IP[i]) + ":" + str(port[i]) + "/bcc.xml")
    devices_offline.append(0)
    print(URL[i])
for i in range(0, 34):
    one_line_values.append(0)
error_message(9)
temporary_short = 0
lines_written = 0
file_date = str(datetime.datetime.now())
file_date = file_date[:10]
days = 0
e_date = datetime.datetime.now() - datetime.timedelta(seconds = ERROR_interval * 60)
First_time = True
while 1:
    lines_written += 1
    for all_files in range(0,len(csv_files)):
        page = 0
        try:
            page = requests.get(URL[all_files], timeout=(1,2))
        except requests.exceptions.ConnectionError:
            time.sleep(10)
            try:
                page = requests.get(URL[all_files], timeout=(2,3))
            except:
                if devices_offline[all_files] == 1:
                    if period > 7:
                        temporary_short = 5
                    continue
                devices_offline[all_files] = 1
                if period > 7:
                    temporary_short = 5
        except requests.exceptions.Timeout:
            print("Connection to device at adress:", IP[all_files], "timed out, trying again with different settings in 10 seconds...")
            logwrite("Connection to device at adress: " + IP[all_files] + " timed out", 1)
            time.sleep(10)
            try:
                page = requests.get(URL[all_files], timeout=(2,3))
            except:
                if devices_offline[all_files] == 1:
                    if period > 7:
                        temporary_short = 5
                    continue
                devices_offline[all_files] = 1
                print("Device at adress:", IP[all_files], "is not responding")
                logwrite("Connection to device at adress: " + IP[all_files] + " timed out again, skiping it", 2)
                if period > 7:
                    temporary_short = 6
        except:
            devices_offline[all_files] = 1
        else:
            if(devices_offline[all_files] == 1):
                print("Device at adress:", IP[all_files], "is back online.")
                logwrite("Device at adress: " + IP[all_files] + " is back online", 0)
                error_message(5)
                devices_offline[all_files] = 0
        if page != 0:
            if page.status_code == 404:
                print("Error 404 (not found), the IP:" , IP[all_files], " is probably wrong.\nPress Enter to exit")
                logwrite("Error 404 (not found), the IP: " + IP[all_files] + " is probably wrong.", 3)
                close_all(len(csv_files))
                quit()
        some_zero = 0
        for i in range(0,len(devices_offline)):
            if devices_offline[i] == 0:
                some_zero = 1
        if devices_offline[all_files] == 1:
            print("Connection to device at adress:", IP[all_files], "FAILED")
            logwrite("Connection to device at adress: " + IP[all_files] + " FAILED", 2)
            error_message(4)
        if some_zero == 0:
            print("Cannot download data from any BCCs")
            logwrite("Cannot download data from any BCCs", 3)
            error_message(6)
            close_all(len(csv_files))
            print("press Enter to exit")
            quit()
        if devices_offline[all_files] == 1:
            continue
        print("Connection to device at adress: ", IP[all_files], " OK")
        if First_time == True:
            logwrite("Connection to device at adress: " + IP[all_files] + " OK", 0)
        listed_file = page.text.split("\n")
        if len(listed_file) != 37:
            print("Device with IP:", IP[all_files], " does not send correct amount of data, maybe the firmware in BCC is not up to date.")
            logwrite("Device with IP:" + IP[all_files] + " does not send correct amount of data, maybe the firmware in BCC is not up to date.", 2)
            continue
        line_number = 0
        column_number = 0
        csv_files[all_files].write(date_time())
        csv_files[all_files].write(";")
        for line in listed_file:
            line_number += 1
            if(line_number > len(listed_file)-1):
                break
            if line_number < 4:
                continue
            split_line = list(line)
            i = 0
            
            while 1:
                if split_line[i] == '>' and split_line[i+1] == 'N':
                    write = 0
                    break
                elif split_line[i] == '>':
                    write = 1
                    break
                i += 1
            i += 1
            write_buffer = ""
            while split_line[i] != '<':
                write_buffer += split_line[i].replace('.',',')
                i += 1
            one_line_values[column_number] = write_buffer
            write_buffer += ";"
            csv_files[all_files].write(write_buffer)
            column_number += 1
        csv_files[all_files].write("\n")
        try:
            one_line_values[0] = float(one_line_values[0].replace(",","."))
            one_line_values[17] = float(one_line_values[17].replace(",","."))
            one_line_values[18] = float(one_line_values[18].replace(",","."))
            one_line_values[21] = float(one_line_values[21].replace(",","."))
            one_line_values[22] = float(one_line_values[22].replace(",","."))
            one_line_values[23] = int(one_line_values[23].replace(",","."))
            one_line_values[24] = int(one_line_values[24].replace(",","."))
            one_line_values[25] = float(one_line_values[25].replace(",","."))
        except:
            if one_line_values[30] != "CONNECTED":
                print("BCC", IP[all_files], "lost connection to CPM, trying again in 10 seconds...")
                logwrite("BCC " + IP[all_files] + " lost connection to CPM, trying again in 10 seconds", 2)
                if (datetime.datetime.now() - e_date).seconds >= ERROR_interval * 60:
                    e_date = datetime.datetime.now()
                    error_message(3)
            else:
                print("Some important values from device:", IP[all_files]," are not a valid numbers, trying again in 10 seconds...")
                logwrite("Some important values from device: " + IP[all_files] + " are not a valid numbers, trying again in 10 seconds", 2)
            time.sleep(10)
            continue
        if one_line_values[0] < daily_limits[all_files][0] or daily_limits[all_files][0] == 0:
            daily_limits[all_files][0] = one_line_values[0]
        if one_line_values[0] > daily_limits[all_files][1] or daily_limits[all_files][1] == 0:
            daily_limits[all_files][1] = one_line_values[0]
        if one_line_values[21] < daily_limits[all_files][2] or daily_limits[all_files][2] == 0:
            daily_limits[all_files][2] = one_line_values[21]
            daily_limits[all_files][4] = one_line_values[23]
        if one_line_values[22] > daily_limits[all_files][3] or daily_limits[all_files][3] == 0:
            daily_limits[all_files][3] = one_line_values[22]
            daily_limits[all_files][5] = one_line_values[24]
        if one_line_values[25] > daily_limits[all_files][6] or daily_limits[all_files][6] == 0:
            daily_limits[all_files][6] = one_line_values[25]

        if one_line_values[21] < one_line_values[17]:
            if (datetime.datetime.now() - e_date).seconds >= ERROR_interval * 60:
                print("Cell", one_line_values[23]," voltage is lower than Umin set on CPM board")
                logwrite("Cell" + str(one_line_values[23]) + " voltage is lower than Umin set on CPM board", 2)
                e_date = datetime.datetime.now()
                es_date = str(e_date)
                error_message(0)

        if one_line_values[22] > one_line_values[18]:
            if (datetime.datetime.now() - e_date).seconds >= ERROR_interval * 60:
                print("Cell", one_line_values[24]," voltage is higher than Umax set on CPM board")
                logwrite("Cell" + str(one_line_values[24]) + " voltage is higher than Umax set on CPM board", 2)
                e_date = datetime.datetime.now()
                es_date = str(e_date)
                error_message(1)

        if one_line_values[25] > Udiff_level and Udiff_level != 0.:
            if (datetime.datetime.now() - e_date).seconds >= ERROR_interval * 60:
                print("Udiff: ", one_line_values[25]," is higher than limit")
                logwrite("Udiff: " + str(one_line_values[25]) + " is higher than limit", 2)
                e_date = datetime.datetime.now()
                es_date = str(e_date)
                error_message(2)
        if one_line_values[21] < Umin_warning:
            if (datetime.datetime.now() - e_date).seconds >= ERROR_interval * 60:
                print("Cell", one_line_values[23]," voltage is lower than Umin set in config file")
                logwrite("Cell" + str(one_line_values[24]) + " voltage is lower than Umin set in config file", 1)
                e_date = datetime.datetime.now()
                es_date = str(e_date)
                error_message(7)
        if one_line_values[22] < Umin_warning:
            if (datetime.datetime.now() - e_date).seconds >= ERROR_interval * 60:
                print("Cell", one_line_values[23],"voltage is higher than Umax set in config file")
                logwrite("Cell" + str(one_line_values[24]) + " voltage is higher than Umax set in config file", 1)
                e_date = datetime.datetime.now()
                es_date = str(e_date)
                error_message(8)
        print("\nBCC", all_files+1, "with adress", IP[all_files])
        print("Actual values:\nTotal voltage:           ", one_line_values[0], "V")
        print("Minimum cell voltage:    ", one_line_values[21], "V", "at position", one_line_values[23])
        print("Maximum cell voltage:    ", one_line_values[22], "V", "at position", one_line_values[24])
        print("Voltage difference:      ", one_line_values[25], "V\n")
        for i in range(0, len(csv_files)):
            csv_files[i].flush()
            lines_written = 0
            os.fsync(csv_files[i].fileno())
    First_time = False
    if file_date != date[:10]:
        days += 1
        server = start_email()
        if server != 0:
            send_to = ""
            for i in range(len(receiver_emails)):
                send_to += receiver_emails[i] + ", "
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = send_to
            message["Subject"] = "Daily report " + subj + " " + file_date
            mess = "Today's peak values:\n\n"
            for i in range(0, len(csv_files)):
                mess += "CPM " + str(i+1) + " with adress "+ IP[i] + "\nMinimum total voltage:       " + str(daily_limits[i][0]) + "V\n"
                mess += "Maximum total voltage:       " + str(daily_limits[i][1]) + "V\n"
                mess += "Minimum cell voltage:        " + str(daily_limits[i][2]) + "V at position " + str(daily_limits[i][4]) + "\n"
                mess += "Maximum cell voltage:        " + str(daily_limits[i][3]) + "V at position " + str(daily_limits[i][5]) + "\n"
                mess += "Maximum voltage difference:  " + str(daily_limits[i][6]) + "V\n\n"
            message.attach(MIMEText(mess, "plain"))
            mess = message.as_string()
            server.sendmail(sender_email, receiver_emails, mess)
            server.quit()
            for x in range(0, len(csv_files)):
                for y in range(0,7):
                    daily_limits[x][y] = 0
        file_date = date[:10]
        if days == File_length:
            logwrite("File length reached, beginning new files")
            close_all(len(csv_files), False)
            days = 0
            for i in range(0, len(csv_files)):
                file_name = date[:10]
                file_name += "_" + str(i) + ".csv"
                csv_files[i] = open(file_name,"w")
    time.sleep(period - temporary_short)
    temporary_short = 0
