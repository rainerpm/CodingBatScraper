# CodingBatScraper

### What the program does

This program prints out the CodingBat results for students that shared their account with a teacher account (see the **Teacher Features** section at https://codingbat.com/help.html)

**The program prints out the following for each student**\
   numCorrect ( 3  9)( 1  3)( ONE )( 2 43) LastName FirstName\
where each set of parenthesis contains the correct and error + incorrect number of submissions for a CodingBat problem in an assignment. NOTE: instead of printing ( 1  0) indicating that the student got it correct the very first time, the program prints ( ONE ).\
Any two subsequent correct submissions that are less than 120 seconds are considered **suspiciously fast** causing the program to print out the fastest two submissions. For example, the below output indicates that p169932 was submitted correctly only 106 seconds after p194781 was submitted correctly.\
  [(106.0, 'p194781', 'p163932'), (128.0, 'p163932', 'p120015')]

**The program will also print out the detailed submission information for a student's submissions.**\
  Problem p194781 (triangle) LastName FirstName\
    2021-04-21 13:18:06  correct\
    2021-04-21 13:23:23  compile error\
    2021-04-21 13:24:10  compile error\
    2021-04-21 13:24:13  compile error\
    2021-04-21 13:24:26  compile error\
    2021-04-21 13:24:43  2/10\
    2021-04-21 13:26:54  compile error\
    2021-04-21 13:29:17  compile error\
    2021-04-21 13:30:40  2/10\
    2021-04-21 13:31:15  0/10to\
    2021-04-21 13:32:33  correct\
    2021-04-21 13:34:31  correct
    
### Required Python packages
  pip install bs4\
  pip install requests

### To make it work for YOUR class
1. To use the program with your CodingBat teacher account enter your login information in the login.py file.
2. In order for the program to identify a student, have the students put identifying information in the Memo field when they share their account with the teacher's account. The program expects this information to be in the format **(P#) YourLastName, YourFirstName** where # is the number of the student's class period. For example, if you were in my Period 5 class and your name was Grace Hopper you would enter **(P5) Hopper, Grace** in the Memo field. You can change the format and content of what the program expects in the Memo field by customizing the memoParse() function.
3. To control which CodingBat problem(s) information is extracted, add an entry to either the **assignments_java** or **assignments_python** dictionary, where the KEY of the dictionary entry is the name of the assignment and the VALUE of the dictionary entry is a dictionary containing CodingBat problems (KEY is the CodingBat problem number from the end of the URL and the VALUE is the name of the problem). See the example Recursion assignment below with 4 CodingBat recursion problems.

   assignments_java["Recursion"] = {"p194781":"triangle","p163932":"sumDigits","p120015":"fibonacci","p118182":"strCopies"}

### Options
* You can optionally choose to extract the code for each students correct submissions to a directory and use the moss program to compare it to all other students code (and if you choose to other solutions - maybe found online - that you have stored in a directory). For this to work you'll have to setup the following variables **DEFAULTOUTPUTDIR** (directory where extracted code will be written to), **MOSSDIR** (directory where the moss.bat and moss.pl files are that are used to run mosss), **ONLINESOLUTIONS** (directory that contains other solutions you want to check your student's code against).

