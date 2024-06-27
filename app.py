from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import json

with open('config.json', 'r') as c:
    params = json.load(c)['params']

app = Flask(__name__)
app.secret_key = 'rishi'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///waterbill.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    
class Customers(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    leftAmt = db.Column(db.Integer, default=0)
    
class Entrys(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(12), nullable=False)

@app.route("/", methods=['GET', 'POST'])
def index():
    message = False
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        msg = request.form.get('msg')
        entry = Contacts(name=name, msg=msg, date=date.today().strftime("%Y-%m-%d"), email=email)
        db.session.add(entry)
        db.session.commit()
        message = True
        
    return render_template('index.html', params=message)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

def sum_value_column():
    result = db.session.query(db.func.sum(Customers.leftAmt)).scalar()
    return result 

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    row = db.session.query(Customers).count()
    result = sum_value_column()
    res = Customers.query.filter_by(leftAmt=0).all()
    error = None
    if ('user' in session and session['user'] == params['admin_user']):
        return render_template('dashboard.html', params=params, row=row, result=result, res=len(res))
    
    if(request.method == "POST"):
        username = request.form.get('uname')
        userpass = request.form.get('password')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username 
            return render_template('dashboard.html', params=params, row=row, result=result, res=len(res))
    
        else:
            error = "Invalid Username or password"
    return render_template('login.html', params=params, error=error, row=row, result=result, res=len(res))

@app.route("/addcustomer", methods=['GET', 'POST'])
def addcustomer():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address') 
        errors = []
        
        if not name:
            errors.append("Please enter your name.")
        if not email:
            errors.append("Please enter your email.")
        if not phone:
            errors.append("Please enter your phone.")
        if not address:
            errors.append("Please enter your address.")
            
        if errors:
            return render_template('addcustomer.html', errors=errors)
        else:
            entry = Customers(name=name, email=email, phone=phone, address=address)
            db.session.add(entry)
            db.session.commit()
            msg = "Customer added successfully."
            return render_template('addcustomer.html', msg=msg)
    return render_template('addcustomer.html')
    

@app.route("/entry", methods=['GET', 'POST'])
def entry():
    today_date = date.today()
    customer = Customers.query.all()
    if(request.method == 'POST'):
        check = request.form.getlist('check')
        for check_id in check:
            res = Customers.query.filter_by(sno=check_id).first()
            newVal = int(res.leftAmt + params['water_price'])
            res.leftAmt = newVal
            today_data = Entrys(name=res.name, date=today_date.strftime("%Y-%m-%d"))
            db.session.add(today_data)
            db.session.commit()
            
    return render_template('entry.html', today_date=today_date.strftime("%d/%m/%Y"), customer=customer)

@app.route("/managecustomer")
def managecustomer():
    customer = Customers.query.all()
    return render_template('managecustomer.html', customer=customer)

@app.route("/update/<int:sno>", methods=['GET', 'POST'])
def update(sno):
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address') 
        amt = request.form.get('leftAmt')
        errors = []
        
        if not name:
            errors.append("Please enter your name.")
        if not email:
            errors.append("Please enter your email.")
        if not phone:
            errors.append("Please enter your phone.")
        if not address:
            errors.append("Please enter your address.")
            
        if errors:
            customer = Customers.query.filter_by(sno=sno).first()
            return render_template('update.html', errors=errors, customer=customer)
        else:
            customer = Customers.query.filter_by(sno=sno).first()
            customer.name = name
            customer.email = email
            customer.phone = phone
            customer.address = address
            customer.leftAmt = amt
            db.session.add(customer)
            db.session.commit()
            msg = "Customer Updated successfully."
            return render_template('update.html', msg=msg, customer=customer)
    
    customer = Customers.query.filter_by(sno=sno).first()
    return render_template('update.html', customer=customer)

@app.route("/delete/<int:sno>")
def delete(sno):
    customer = Customers.query.filter_by(sno=sno).first()
    db.session.delete(customer)
    db.session.commit()
    return redirect("/managecustomer")

@app.route("/bill")
def bill():
    data_dict = {}
    customer = Customers.query.all()
    entries = Entrys.query.all()
    for entry in entries:
        if entry.name in data_dict:
            data_dict[entry.name].append(entry.date)
        else:
            data_dict[entry.name] = [entry.date]
    return render_template('bill.html', data_dict=data_dict, customer=customer)



@app.route("/create_tables")
def create_tables():
    with app.app_context():
        db.create_all()
    return "Tables created successfully!"

if __name__ == "__main__":
    app.run(debug=True)
