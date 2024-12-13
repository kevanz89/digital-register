
from flask import *
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import re
# from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key=os.urandom(16).hex()
app.config['SESSION_TYPE']='filesystem'


def get_connection():
    try:

      return mysql.connector.connect(host="localhost",user="root",password="",database="classroom")
    except Exception as e:
        print(f"An error occured while connecting to the database.",{str(e)}) 
        return None


connection=get_connection()

def fetch_scheduled_classes():
    current_day = datetime.now().strftime('%A')
    current_time = datetime.now().time()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT subject, lesson_time FROM class_schedule 
        WHERE day_of_week = %s AND lesson_time = %s
    """, (current_day, current_time))

    scheduled_classes = cursor.fetchall()
    cursor.close()
    connection.close()
    return scheduled_classes

def valid_reg_no(reg_no):
    reg_no_pattern=r'^[A-Z]{2}\d{3}/G/\d{5}/\d{2}$'
    return re.match(reg_no_pattern,reg_no)

CLASS_START_TIME = "10:00"
CLASS_END_TIME = "23:00"    

@app.route('/')
def preloader():
    return render_template('preloader.html')
@app.route('/register')
def home():
    return render_template('register.html')

@app.route('/sign_in',methods=['GET','POST'])
def sign_in():
    student_name = None 
    lessons=[]
    cursor = None
    connection=get_connection()
    if connection is None:
        flash("Database connection error.")
        return redirect(url_for('home'))
    try:
        if request.method == 'POST': 
            reg_no = request.form['reg_no']
            student_name = request.form['student_name'] 
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        

              
            if not valid_reg_no(reg_no) or not student_name:
                flash("Invalid Credentials; kindly check registration number or student name.")
                return redirect(url_for('home'))   
            current_time = datetime.now().time()
            start_time = datetime.strptime(CLASS_START_TIME, '%H:%M').time()
            end_time = datetime.strptime(CLASS_END_TIME, '%H:%M').time()

            
            if not (start_time <=current_time <= end_time):  
                flash("Class not ongoing! You can't join the class.") 
                return redirect(url_for('home'))                 

            cursor = connection.cursor()  
            cursor.execute("SELECT * FROM attendance WHERE reg_no=%s", (reg_no,))
            existing_student = cursor.fetchone()

            if existing_student:
                flash("Student has already signed in!")
            else:
                try:
                    
                  
                     cursor.execute("INSERT INTO attendance (reg_no, student_name, timestamp) VALUES (%s, %s, %s)",(reg_no, student_name, timestamp))
                     connection.commit()

                     cursor.execute("SELECT unit, lesson_time FROM lessons WHERE reg_no=%s AND date=CURRENT_DATE", (reg_no,))
                     lessons = cursor.fetchall()
             
                    
                except Exception as e:
                    connection.rollback()
                    flash(f"An error occurred: {str(e)}")
                    return redirect(url_for('home')) 

            return redirect(url_for('thanks', student_name=student_name, lessons=lessons))

    except Exception as e:
        flash(f"An error occurred: {str(e)}")

    finally:
        if cursor is not None:
            cursor.close()

    return render_template('register.html')

@app.route('/feedback')
def thanks():
    student_name=request.args.get('student_name','')
    lessons=request.args.get('lessons',[])
    return render_template('feedback.html',student_name=student_name,lessons=lessons)
@app.route('/admin',methods=['GET','POST'])
def admin():

    
    
    if session.get('logged_in'):
        
        return redirect(url_for('check_register'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

               
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            session['username'] = username
            
            return redirect(url_for('check_register'))  
        else:
            flash("Invalid credentials! Please try again!")
            
            return redirect(url_for('admin'))  

    return render_template('admin.html') 

@app.route('/check_register')
def check_register():
    if not session.get('logged_in'):
        flash("You must be logged in to view the register.")
        return redirect(url_for('admin'))
    connection=get_connection()
    cursor=connection.cursor()

    try:
        cursor.execute("SELECT * FROM attendance")
        result=cursor.fetchall()
        

        if not result:
            return "No attendance record found",404
        return render_template('check_register.html',result=result)
    except Exception as e:
        print(f"Database error: {e}")  
        return "An error occurred while fetching attendance records.", 500

    finally:
        cursor.close()
        connection.close() 
@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    return redirect(url_for('admin'))

if __name__== '__main__':
    app.run(debug=True)

