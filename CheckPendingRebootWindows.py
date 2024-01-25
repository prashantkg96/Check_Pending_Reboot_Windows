
import subprocess
import pandas as pd
import time
from io import StringIO
import re
import datetime
import os
from pathlib import Path


def main_func(modulePath):
    modulePath = Path(modulePath)
    
    strToFindPath = "WindowsUpdate.log written to "
    strToFindRestart = "Reboot required = True"
    
    powershellPath = Path(r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe')

    result = subprocess.run([powershellPath, r'Get-WindowsUpdateLog'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    pathOut = Path(str(result)[str(result).find(strToFindPath) + len(strToFindPath):-8].strip())
    df = pd.read_csv(pathOut, header=None, sep='\t')
    time.sleep(10)   # Timer used to complete onedrive sync and avoid sync conflict
    os.remove(pathOut)
    

    #Handle last reboot date to current date list
    result = subprocess.run([powershellPath, r'Get-CimInstance -ClassName win32_operatingsystem | select csname, lastbootuptime'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    regex_pattern = r"([\d]{1,2}/[\d]{1,2}/[\d]{4}) (\d{1,2}:\d{2}:\d{2} [APM]{2})"
    lastRebootStamp = re.findall(regex_pattern,str(result.stdout))
    lastRebootDate = lastRebootStamp[0][0]
    lastRebootTime = lastRebootStamp[0][1]
    lastRebootDateTime = datetime.datetime.strptime(lastRebootDate + " " + lastRebootTime, "%m/%d/%Y %I:%M:%S %p")
    
    
    #Check if reboot is needed, if so then ping on teams
    for i in range(len(df)):
        thisRow= df[0][i]
        thisDateTime_String = str(thisRow).split()[0].strip() + " " + str(thisRow).split()[1].strip().split(".")[0].strip()
        thisDateTime = datetime.datetime.strptime(thisDateTime_String, "%Y/%m/%d %H:%M:%S")
        if strToFindRestart in thisRow and thisDateTime > lastRebootDateTime:
            curr_time = datetime.datetime.now()
            ping_timedelta = 0
            
            try:
                stored_time_str = ""
                with open(Path.joinpath(modulePath, "Restart_Ping.txt"), 'r') as file:
                    stored_time_str = file.read()
                stored_time_str = datetime.datetime.strptime(stored_time_str, "%Y-%m-%d %H:%M:%S.%f")
                ping_timedelta = curr_time - stored_time_str
                ping_timedelta = ping_timedelta.total_seconds()/60/60
            except:
                with open(Path.joinpath(modulePath, "Restart_Ping.txt"), 'w') as file:
                    file.write(str(curr_time))
            
            if ping_timedelta >= 3: # Will ping if last ping was atleast 3 hours later. Helps reduce spamming
                print(f"Last reboot : {lastRebootDateTime}")
                print(f"Reboot required at : {thisDateTime}")
                print("Reboot required!")
                # Add additional functions here to execute when script detects a pending reboot
                
                with open(Path.joinpath(modulePath, "Restart_Ping.txt"), 'w') as file:
                    file.write(str(curr_time))
            break


if __name__ == "__main__":
    this_modulePath = os.getcwd()
    main_func(this_modulePath)


