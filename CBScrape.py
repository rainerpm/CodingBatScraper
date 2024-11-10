from login import codingBatLoginUserName, codingBatLoginPassword
from CBScrapedata import DEFAULTOUTPUTDIR,MOSSDIR,ONLINESOLUTIONS,SCOREBOARDDIR,PERIODSPYTHON,PERIODSJAVA,assignments_java,assignments_python

from bs4 import BeautifulSoup   # Thonny (import beautifulsoup4)
import requests  # import request
import getpass
import re
from datetime import datetime
import os
from shutil import copyfile
from shutil import copy      # module is in python standard library
from pathlib  import Path

dateTime = datetime.now().strftime("%b_%d_%Hh%Mm%Ss")

class bcolors:
    BLUE = '\033[94m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# extract student's class period and first & last name from info in memo field
def memoParse(memo):
   result = re.search('^\((.*)\) ([-\w]+),\s?([-\w]+) (\d+)', memo)
   studentPeriod = lastName = firstName = studentId = ""
   if result:
      studentPeriod = result.group(1)
      lastName = result.group(2)
      firstName = result.group(3)
      studentId = result.group(4)
   else:
      result = re.search('^\((.*)\) ([-\w]+),\s?([-\w]+)', memo)
      if result:
          studentPeriod = result.group(1)
          lastName = result.group(2)
          firstName = result.group(3)
          studentId = bcolors.BOLD + bcolors.RED + "***NoStudentId***" + bcolors.ENDC         
   return studentPeriod,lastName,firstName,studentId
   
def scrapeStudentData(session,period,problems):
    for key in sorted(problems.keys()) :
       print(" ",key , " -> " , problems[key])
    print("Retrieving student data (correct, error + incorrect)")
    studentsData = []
    reportPage = session.get(REPORT_URL)
    soup = BeautifulSoup(reportPage.content,"html.parser")
    table_data = soup.find_all("table")[2]   # table of students
    table_rows = table_data.find_all("tr")
    for table_row in table_rows[2:]:      # each row is a student
       tds = table_row.find_all("td",limit=2)
       email = tds[0].text
       memo = tds[1].text.replace("  ", " ")    # 2nd <td> is the memo column (sometimes an extra space creeps in btw comma and first name, even if it isn't there in the memo field)
       studentPeriod,lastName,firstName,studentId = memoParse(memo)
       #print(">>>",lastName,firstName)
       if studentPeriod and (studentPeriod == period):
          link = tds[0].find("a")         # 1st <td> is the link
          href = link.get('href')
          # check status of problems (see if student finished problems in problems list)
          studentSubmissionsUrl = BASE_URL + href
          response = session.get(studentSubmissionsUrl)
          content = BeautifulSoup(response.content,"html.parser")
          # extract the value of the javascript variable problems in the script on
          # the students results page (to see do right click and View Page Source. 
          # create a python list which has a dictionary for each solved problem
          scriptProblemsVar = content.find_all("script")[0].string 
          scriptProblemsVar = scriptProblemsVar.replace("},]","}]")
          scriptProblemsVar = scriptProblemsVar.replace("{id:","{'id':")
          scriptProblemsVar = scriptProblemsVar.replace("{d:","{'d':")
          scriptProblemsVar = scriptProblemsVar.replace(" s:"," 's':")
          scriptProblemsVar = scriptProblemsVar.replace("attempts:","'attempts':")
          #print(scriptProblemsVar)
          if ',' in scriptProblemsVar:
             scriptProblemsVar = scriptProblemsVar[:scriptProblemsVar.rindex(',')] + scriptProblemsVar[scriptProblemsVar.rindex(',')+1:]
          scriptProblemsVar = scriptProblemsVar.split('=')[1].rstrip(";")
          studentProblemsList = eval(scriptProblemsVar)
          studentProblemsDict = {}
          for studentProblem in studentProblemsList:
             attemptsRaw = []
             for attempt in studentProblem['attempts']:
                attemptsRaw.append((attempt['d'],attempt['s']))
             attempts = []     # with DateTime object instead of DateTime string
             for attempt in attemptsRaw:
                 attempts.append((datetime.strptime(attempt[0], '%Y%m%d-%H%M%Sz'),attempt[1]))
             attempts.sort()
             #print(attempts)
             #exit()
             studentProblemsDict[studentProblem['id']] = attempts

          ## extract code for problems (4/24/21 look at again later)
          studentExtractedCodeDict = {}
          if EXTRACTFILES:
             # extract programs   
             userEmail = re.search('user=(.*)&tag', href).group(1)
             for problem in problems:
                studentProblemURL = BASE_URL + "/prob/" + problem + "?owner=" + userEmail
                response = session.get(studentProblemURL)
                content = BeautifulSoup(response.content,"html.parser")
                indentDiv = content.find(class_="indent")
                table = indentDiv.find("form", {"name": "codeform"})
                aceDiv = table.find("div", id="ace_div")
                studentExtractedCodeDict[problem] = aceDiv.text
          studentsData.append((studentPeriod,lastName,firstName,email,studentProblemsDict,studentExtractedCodeDict,studentId))      
    studentsData.sort()
    return studentsData

def attemptsStats(attempts):
   compileErrors = correctRuns = incorrectRuns = 0
   for attempt in attempts:
     if attempt[1][0] == 'c':
        compileErrors += 1
     elif attempt[1][0] == 's':
        correctRuns += 1
     elif attempt[1][0] == 't':
        incorrectRuns +=1
   incorrectRuns += compileErrors 
   return correctRuns,incorrectRuns

def firstCorrectAttempt(attempts):
    for attempt in attempts:
        if attempt[1][0] == 's':
            return attempt

def attemptsAddDifference(attempts):    # add time difference to next attempt to each attempt (except last attempt of course)
    first = True
    attemptsWithDiff = []
    for attempt in attempts:
        if first:
            dateTime1 = attempt[0]
            problem1 = attempt[1]
            first = False
        else:
            difference = attempt[0] - dateTime1
            attemptsWithDiff.append((difference.total_seconds(),problem1,attempt[1]))
            dateTime1 = attempt[0]
            problem1 = attempt[1]
    return attemptsWithDiff           

def attemptInterpret(attempt):
    if attempt[1][0] == 'c':
      result = "compile error"
    elif attempt[1][0] == 's':
      result = "correct"
    elif attempt[1][0] == 't':
      result = attempt[1][1:]        
    return str(attempt[0]) + "  " + result

def processScrapedData(scrapedData,problems,studentDetails):
  currentDateTime = datetime.now().strftime("%Y_%b_%d")
  year2Digits = datetime.now().strftime("%y")

  count = 0
  firstWrite = True
  for studentData in scrapedData:
     studentPeriod = studentData[0]
     studentName = studentData[1]+" "+studentData[2]
     studentId = studentData[6]
     count = count + 1
     results = ""
     numCorrect = 0
     studentProblemsDict = studentData[4]
     firstCorrectAttempts = []
     for problem in problems:
        if problem in studentProblemsDict:
          attempts = studentProblemsDict[problem]
          c,i = attemptsStats(attempts)
          result = f'({c:2d} {i:2d})'
          if result == "( 1  0)":
            result = bcolors.BOLD + bcolors.RED + "( ONE )" + bcolors.ENDC
          if result == "( 1  1)":
            result = bcolors.BOLD + bcolors.BLUE + "( TWO )" + bcolors.ENDC
          if c > 0:
            numCorrect += 1
          first = firstCorrectAttempt(attempts)
          if first:
              firstCorrectAttempts.append((first[0],problems[problem]))   # correct attempt time it was first correct and the problem name
        else:
            result = "(!done)"
        results += result
     outputStr = f'{count:>2d} {studentData[0]} {numCorrect:>2d} {results} {studentName} {studentId}'
     print(outputStr)
     if (firstWrite):
         firstWrite = False
         with open(Path(SCOREBOARDDIR,studentData[0] + ' - ' + assignmentName + '.txt'), "w") as gf:
             gf.write(outputStr+'\n')
     else:
         with open(Path(SCOREBOARDDIR,studentData[0] + ' - ' + assignmentName + '.txt'), "a") as gf:
             gf.write(outputStr+'\n')             
     if firstCorrectAttempts:
        firstCorrectAttempts.sort()
        firstCorrectAttemptsWithDifference = attemptsAddDifference(firstCorrectAttempts)
        if firstCorrectAttemptsWithDifference:
           firstCorrectAttemptsWithDifference.sort()
           first = firstCorrectAttemptsWithDifference[0]
           if FASTSUBMISSIONS and first[0] < 120:
              print("        ",firstCorrectAttemptsWithDifference[:2])
  print('Wrote results to file ' + str(Path(SCOREBOARDDIR,studentData[0] + ' - ' + assignmentName + '.txt')))
  
  if EXTRACTFILES:
      print("Extracting files to",OUTPUTDIR)
      ## write out code for each problem
      if not os.path.isdir(OUTPUTDIR):
         os.mkdir(OUTPUTDIR)
         print("Created",OUTPUTDIR)
      for problem in problems:
         problemDir = OUTPUTDIR + "/" + problems[problem]
         if not os.path.isdir(problemDir):
            os.mkdir(problemDir)
            print("new directory",problemDir)
         os.chdir(problemDir)
         extractToDir = os.path.join(problemDir,currentDateTime)
         if not os.path.isdir(currentDateTime):
             os.mkdir(currentDateTime)
         os.chdir(currentDateTime)
         copyfile(MOSSDIR + "/" + MOSS_BAT_FILE,extractToDir + "/moss.bat")            
         copyfile(MOSSDIR + "/moss.pl",extractToDir + "/moss.pl")            
         for studentData in scrapedData:
            lastName  = studentData[1]
            firstName = studentData[2]
            extractedCodeDict = studentData[5]
            extractedCode = extractedCodeDict.get(problem,"// not done")
            fileName = year2Digits + '_' + studentPeriod + lastName + firstName
            with open(extractToDir + "/" + fileName + FILE_EXT, "w", encoding="utf-8") as f:   
               f.write(extractedCode)
         ONLINESOLUTIONSDIR = os.path.join(ONLINESOLUTIONS,language,problem + "_" + problems[problem])
         if os.path.isdir(ONLINESOLUTIONSDIR):
             print(f'  copying online solutions files from {ONLINESOLUTIONSDIR}')
             print(f'  to {problemDir} for running moss.')
             files = os.listdir(ONLINESOLUTIONSDIR)
             for fname in files:
                copy(os.path.join(ONLINESOLUTIONSDIR,fname),extractToDir)
      #print("  copy online solution files from")
      #print("   ",ONLINESOLUTIONS)
      #print("  to the extracted file directory")
      #print("   ",OUTPUTDIR)
      #print("  and then run moss")
     
  while studentDetails:
      ans = input("Enter number for student details (or x to exit)? ")
      if ans == 'x':
          exit()
      studentData = scrapedData[int(ans)-1]
      studentProblemsDict = studentData[4]
      print(problems)
      for problem in problems:
        if problem in studentProblemsDict:
          print("Problem",problem,"("+problems[problem]+")",studentData[2],studentData[1])
          attempts = studentProblemsDict[problem]
          for attempt in attempts:
             print(" ",attemptInterpret(attempt))
      

if __name__ == "__main__":
    if not Path(SCOREBOARDDIR).is_dir():
        Path(SCOREBOARDDIR).mkdir()    
    PERIODS = PERIODSJAVA + PERIODSPYTHON
    print("Python Classes")
    for periodopt in PERIODSPYTHON:
        print(f'  {periodopt[-1]}) {periodopt}')
    print("JAVA Classes")
    for periodopt in PERIODSJAVA:
        print(f'  {periodopt[-1]}) {periodopt}')
    #choice = input("Choose period(s)? ")
    #PERIOD = "P" + str(choice)
    userInput = input('For a language choose one or more numbers (separated with space) (x=exit): ').strip()
    if userInput == 'x':
        exit() 
    selected = userInput.split()
    periodsSelected = ["P" + s for s in selected]
    
    assignments = assignments_java
    language = "java"
    if periodsSelected[0] in PERIODSPYTHON:
        language = "python"
        assignments = assignments_python
        
    assignmentsList = list(assignments.items())
    opt = 1
    for assignment in assignmentsList:
        print(f'  {opt}) {assignment[0]}')
        opt += 1
    userInput = input("Choose one or more assignments (separated by spaces)? ")
    assignmentsSelected = userInput.split()
       
    ans = input("Print out suspiciously fast submissions (y)? ")
    if ans == 'y':
       FASTSUBMISSIONS = True
    else:
       FASTSUBMISSIONS = False

    ans = input("Extract code for plagiarism checking (y)? ")
    if ans == 'y':
       EXTRACTFILES = True
       OUTPUTDIR = os.path.join(DEFAULTOUTPUTDIR,assignmentName)
    else:
       EXTRACTFILES = False
       
    # urls to use
    BASE_URL = "https://codingbat.com"
    LOGIN_URL = BASE_URL + "/login"
    if language == "java":
       LANGUAGE_URL = BASE_URL + "/java"
       REPORT_URL = BASE_URL + "/report?java=on&stock=on&sortname=on&homepath=&form="
       COMMENT_START = "//"
       FILE_EXT = ".java"
       MOSS_BAT_FILE = "moss_java.bat"
    else:
       LANGUAGE_URL = BASE_URL + "/pytPath(SCOREBOARDDIRhon"
       REPORT_URL = BASE_URL + "/report?python=on&stock=on&sortname=on&homepath=&form="
       COMMENT_START = "#"
       FILE_EXT = ".py"
       MOSS_BAT_FILE = "moss_python.bat"
    post_params = {
        "uname": codingBatLoginUserName,
        "pw": codingBatLoginPassword,
    }
    with requests.Session() as session:
        print("Logging in")
        post = session.post(LOGIN_URL, data=post_params)
        if "Failed to login -- bad username or password" in post.text:
           print("  login failed (double check CodingBat username & password in login.py)")
           exit()
            
        for period in periodsSelected:
            for assignment in assignmentsSelected:
                assignmentName = assignmentsList[int(assignment)-1][0]
                problems = assignmentsList[int(assignment)-1][1]               
                print("\n"+ bcolors.BOLD + "*** CLASS PERIOD " + period + " (" + assignmentName + ") ***" + bcolors.ENDC)
                scrapedData = scrapeStudentData(session,period,problems)
                processScrapedData(scrapedData,problems,len(periodsSelected)==1 and len(assignmentsSelected)==1)
