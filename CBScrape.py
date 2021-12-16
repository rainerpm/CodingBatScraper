from login import codingBatLoginUserName, codingBatLoginPassword

from bs4 import BeautifulSoup
import requests
import getpass
import re
from datetime import datetime
import os
from shutil import copyfile

# CONSTANTS to setup
# set below to True if you only want output from specific class period(s)
# You will have to update the memoParse() function below to extract
# the class period info from the memo field on the CodingBat report page
FILTERBYPERIOD = True  
# If you choose to extract files you'll also need to setup these
DEFAULTOUTPUTDIR = "C:/Users/E151509/Desktop/misc/CodingBatResults"
MOSSDIR = "C:/Users/E151509/Google Drive/My LASA/misc/tools/moss plagiarize checking"
ONLINESOLUTIONS = "C:/Users/E151509/Google Drive/My LASA/CodingBat/Plagiarism/"

#                                    "":"", "":"", "":"",


###### JAVA ######
assignments_java = {}
assignments_java["String Excercises"] = {"p161056" : "makeAbba", "p147483" : "makeTags","p184030" : "makeOutWord","p108853" : "extraEnd","p172267" : "firstHalf","p130896" : "withoutEnd","p143825" : "nonStart","p197720" : "left2","p137729" : "middleTwo","p174148" : "nTwice","p115863" : "middleThree","p194786" : "lastTwo"}
assignments_java["Aa-Logic80%"] = {"p159531" : "cigarParty","p103360":"dataFashion","p141061":"squirrelPlay","p160543":"alarmClock","p193613":"nearTen","p110973":"answerCell","p153748":"shareDigit"}
assignments_java["Ab-Logic90%"] = {"p177181":"teaParty","p137136":"fizzString","p115243":"fizzString2","p113261":"twoAsOne"}
assignments_java["Ac-Logic100%"] = {"p154188":"inOrder","p140272":"inOrderEqual","p169213":"lastDigit","p179196":"lessBy10","p115384":"maxMod5"}
assignments_java["Ba-Arrays80%"] = {"p167011":"makePi","p101230":"makeEnds","p171022":"has23",
                                    "p111327":"sum67", "p180920":"fizzArray", "p159979":"modThree",
                                    "p105031":"shiftLeft", "p199484":"tenRun"}
assignments_java["Bb-Arraysjust100%"] = {"p189576":"maxSpan","p158767":"canBalance","p104090":"seriesUp"}
assignments_java["Bb-Arrays80%and100%"] = {"p167011":"makePi","p101230":"makeEnds","p171022":"has23",
                                    "p111327":"sum67", "p180920":"fizzArray", "p159979":"modThree",
                                    "p105031":"shiftLeft", "p199484":"tenRun",
                                    "p189576":"maxSpan","p158767":"canBalance","p104090":"seriesUp"}
assignments_java["Challenge 1"] = {"p271468":"myParseInt","p287839":"noRepeatSubSeq"}
assignments_java["Midterm"] = {"p283631" : "isAlphaNumeric", "p292285" : "whatFloor"}
assignments_java["Flex Friday"] = {"p136585":"centeredAverage"}
assignments_java["Recursion"] = {"p194781":"triangle","p163932":"sumDigits","p120015":"fibonacci","p118182":"strCopies"}

      
###### PYTHON ######
assignments_python = {}
assignments_python["A_warmup"] = {"p166884" : "parrot_trouble", "p124984" : "makes10", "p124676" : "near_hundred", "p162058" : "pos_neg"}
assignments_python["B_logic"] = {"p129125" : "date_fashion", "p135815" : "squirrel_play", "p119867" : "alarm_clock"}
assignments_python["C_berlinWall"] = {"p225759" : "berlinWall0", "p215725" : "berlinWall1", "p212912" : "berlinWall2"}
assignments_python["rightRange"] = {"p299949" : "rightRange"}
assignments_python["strings1"] = {"p115413" : "hello_name","p182144" : "make_abba","p132290" : "make_tags","p129981" : "make_out_word","p148853" : "extra_end","p184816" : "first_two","p107010" : "first_half","p138533" : "without_end","p194053" : "combo_string","p127703" : "non_start","p160545" : "left2"}
assignments_python["list bonus"] = {"p192962":"reverse3","p135290":"max_end3","p126968":"centered_average","p108886":"sum67"}
assignments_python["Final 2021 - Day 1"] = {"p255003" : "div2and7","p281953" : "allAboutListsPart1"}  
assignments_python["Final 2021 - Day 2"] = {"p226557" : "allAboutListsPart2","p217373" : "allAboutListsPart3"}


# extract student's class period and first & last name from info in memo field
def memoParse(memo):
   result = re.search('^\((.*)\) ([-\w]+),\s?([-\w]+)', memo)
   studentPeriod = lastName = firstName = ""
   if result:
      studentPeriod = result.group(1)
      lastName = result.group(2)
      firstName = result.group(3)
   return studentPeriod,lastName,firstName
   
# scrapes home page for each directories title to be used in url building
def scrapeStudentsData(session):
    for key in sorted(PROBLEMS.keys()) :
       print(" ",key , " -> " , PROBLEMS[key])
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
       studentPeriod,lastName,firstName = memoParse(memo)
       #print(">>>",lastName,firstName)
       if not FILTERBYPERIOD or (studentPeriod and (studentPeriod in PERIOD)):
          link = tds[0].find("a")         # 1st <td> is the link
          href = link.get('href')
          # check status of problems (see if student finished problems in PROBLEMS list)
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
             for problem in PROBLEMS:
                studentProblemURL = BASE_URL + "/prob/" + problem + "?owner=" + userEmail
                response = session.get(studentProblemURL)
                content = BeautifulSoup(response.content,"html.parser")
                indentDiv = content.find(class_="indent")
                table = indentDiv.find("form", {"name": "codeform"})
                aceDiv = table.find("div", id="ace_div")
                studentExtractedCodeDict[problem] = aceDiv.text
          studentsData.append((studentPeriod,lastName,firstName,email,studentProblemsDict,studentExtractedCodeDict))      
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

# login to site, process results, and write out submitted code
def doIt():
   currentDateTime = datetime.now().strftime("%b_%d_%Hh%Mm")
   with requests.Session() as session:
      print("Logging in")
      post = session.post(LOGIN_URL, data=post_params)
      if "Failed to login -- bad username or password" in post.text:
           print("  login failed (double check CodingBat username & password in login.py)")
           exit()
      scrapedData = scrapeStudentsData(session)
      count = 0
      for studentData in scrapedData:
         studentName = studentData[1]+" "+studentData[2]
         count = count + 1
         results = ""
         numCorrect = 0
         studentProblemsDict = studentData[4]
         firstCorrectAttempts = []
         for problem in PROBLEMS:
            if problem in studentProblemsDict:
              attempts = studentProblemsDict[problem]
              c,i = attemptsStats(attempts)
              result = f'({c:2d} {i:2d})'
              if result == "( 1  0)":
                result = "( ONE )"
              if c > 0:
                numCorrect += 1
              first = firstCorrectAttempt(attempts)
              if first:
                  firstCorrectAttempts.append((first[0],problem))   # correct attempt time it was first correct and the problem name
            else:
                result = "(!done)"
            results += result
         print(f'{count:>2d} {studentData[0]} {numCorrect:>2d} {results} {studentName}')
         if firstCorrectAttempts:
            firstCorrectAttempts.sort()
            firstCorrectAttemptsWithDifference = attemptsAddDifference(firstCorrectAttempts)
            if firstCorrectAttemptsWithDifference:
               firstCorrectAttemptsWithDifference.sort()
               first = firstCorrectAttemptsWithDifference[0]
               if FASTSUBMISSIONS and first[0] < 120:
                  print("        ",firstCorrectAttemptsWithDifference[:2])

      if EXTRACTFILES:
          print("Extracting files to",OUTPUTDIR)
          ## write out code for each problem
          if not os.path.isdir(OUTPUTDIR):
             os.mkdir(OUTPUTDIR)
             print("Created",OUTPUTDIR)
          for problem in PROBLEMS:
             problemDir = OUTPUTDIR + "/" + problem
             if not os.path.isdir(problemDir):
                os.mkdir(problemDir)
                print("new directory",problemDir)
             os.chdir(problemDir)
             extractToDir = os.path.join(problemDir,currentDateTime)
             os.mkdir(currentDateTime)
             os.chdir(currentDateTime)
             copyfile(MOSSDIR + "/" + MOSS_BAT_FILE,extractToDir + "/moss.bat")            
             copyfile(MOSSDIR + "/moss.pl",extractToDir + "/moss.pl")            
             for studentData in scrapedData:
                lastName  = studentData[1]
                firstName = studentData[2]
                extractedCodeDict = studentData[5]
                extractedCode = extractedCodeDict.get(problem,"// not done")
                fileName = lastName + firstName
                with open(extractToDir + "/" + fileName + FILE_EXT, "w", encoding="utf-8") as f:   
                   f.write(extractedCode)
          print("  copy online solution files from")
          print("   ",ONLINESOLUTIONS)
          print("  to the extracted file directory")
          print("   ",OUTPUTDIR)
          print("  and then run moss")

      while True:
          ans = input("Enter number for student details (or x to exit)? ")
          if ans == 'x':
              exit()
          studentData = scrapedData[int(ans)-1]
          studentProblemsDict = studentData[4]
          print(PROBLEMS)
          for problem in PROBLEMS:
            if problem in studentProblemsDict:
              print("Problem",problem,"("+PROBLEMS[problem]+")",studentData[2],studentData[1])
              attempts = studentProblemsDict[problem]
              for attempt in attempts:
                 print(" ",attemptInterpret(attempt))
          

if __name__ == "__main__":
    assignments = assignments_java
    language = "java"

    if FILTERBYPERIOD:
        PERIODSPYTHON = ["P1","P2","P5","P6","P1P2P5P6"]
        PERIODSJAVA = ["P8"]
        PERIODS = PERIODSJAVA + PERIODSPYTHON
        opt = 1
        for periodopt in PERIODS:
            print(str(opt) + ")" ,periodopt)
            opt += 1
        choice = input("Choose period(s)? ")
        PERIOD = PERIODS[int(choice)-1]

        if PERIOD in PERIODSPYTHON:
            language = "python"
            assignments = assignments_python
        
    assignmentsList = sorted(assignments.items())

    opt = 1
    for assignment in assignmentsList:
        print(str(opt) + ")" , assignment[0])
        opt += 1
    choice = input("Choose assignment? ")
    PROBLEMS = assignmentsList[int(choice)-1][1]

    ans = input("Print out suspiciously fast submissions (y or ENTER to continue)? ")
    if ans == 'y':
       FASTSUBMISSIONS = True
    else:
       FASTSUBMISSIONS = False

    ans = input("Extract code for plagiarism checking (n or ENTER to continue)? ")
    if ans == 'n':
       EXTRACTFILES = False
    else:
       EXTRACTFILES = True
       OUTPUTDIR = DEFAULTOUTPUTDIR 
                
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
       LANGUAGE_URL = BASE_URL + "/python"
       REPORT_URL = BASE_URL + "/report?python=on&stock=on&sortname=on&homepath=&form="
       COMMENT_START = "#"
       FILE_EXT = ".py"
       MOSS_BAT_FILE = "moss_python.bat"
    post_params = {
        "uname": codingBatLoginUserName,
        "pw": codingBatLoginPassword,
    }
    doIt()
