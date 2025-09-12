from flask import Flask, redirect, url_for, render_template, flash, request,url_for,session,logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators 
from passlib.hash import sha256_crypt
app = Flask(__name__)   

def articulos():
    return [
        {"titulo": "Artículo 1", "contenido": "Contenido del artículo 1"},
        {"titulo": "Artículo 2", "contenido": "Contenido del artículo 2"}
    ]



@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/movimientos')
def movimientos():
    return render_template('movimientos.html')

@app.route('/reportes')
def reportes():
    return render_template('reportes.html', articulos=articulos())

class RegistroForm(Form):
    name = StringField('Nombre', [validators.Length(min=1, max=50)])
    username = StringField('Usuario', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=10, max=50)])
    password = PasswordField('Contraseña', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Las contraseñas no coinciden')
    ])
    confirm = PasswordField('Confirmar Contraseña') 

@app.route('/register', methods=['GET', 'POST'])    
def register():
    form = RegistroForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        flash('¡Te has registrado correctamente!', 'success')
        return redirect(url_for('inicio'))
    
    return render_template('register.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)