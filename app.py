from flask import Flask, redirect, url_for, render_template, flash, request, url_for, session
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from datetime import datetime
from functools import wraps


app = Flask(__name__)   

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '2008'
app.config['MYSQL_DB'] = 'agroprime'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = 'hola123'

# Inicializar MySQL
mysql = MySQL(app)


class RegistroForm(Form):
    name = StringField('Nombre', [validators.Length(min=1, max=50)])
    username = StringField('Usuario', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Contraseña', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Las contraseñas no coinciden')
    ])
    confirm = PasswordField('Confirmar Contraseña')

class LoginForm(Form):
    username = StringField('Usuario', [validators.Length(min=4, max=25)])
    password = PasswordField('Contraseña', [validators.DataRequired()])


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Por favor inicia sesión', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/')
@is_logged_in
def inicio():
    # Obtener el user_id de la sesión actual
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor()
    # FILTRAR movimientos solo del usuario actual
    cur.execute("SELECT * FROM movimientos WHERE user_id = %s ORDER BY fecha DESC", (user_id,))
    resul = cur.fetchall()
    
    print(f"Usuario: {session.get('name')} - Movimientos: {len(resul)}")

    # Calcular el monto total solo de los movimientos del usuario
    monto_total = 0
    for i in resul:
        montos_guardados = float(i['monto'])
        tipo = i['tipo']
        if tipo == 'ingreso':
            monto_total += montos_guardados
        else: 
            monto_total -= montos_guardados
    
    print(f"Monto total del usuario {session.get('name')}: {monto_total}")
    cur.close()
    
    return render_template('inicio.html', movimientos=resul, monto_total=monto_total)


    

@app.route('/movimientos', methods=['GET','POST'])
@is_logged_in
def movimientos():
    if request.method == 'POST':
        
        # Obtener datos del formulario
        fecha = request.form['fecha']
        tipo = request.form['tipo']
        vrunidad = float(request.form['vrunidad'])  # Del HTML
        cantidad = float(request.form['cantidad'])  # Del HTML
        descripcion = request.form.get('descripcion')
        monto = round(vrunidad * cantidad, 2)
        
        cur = mysql.connection.cursor()
        
        # Insertar movimientos asociados al usuario actual
        cur.execute(""" INSERT INTO movimientos (user_id, fecha, tipo, monto, descripcion)
        VALUES (%s, %s, %s, %s, %s)
        """, (int(session['user_id']), str(fecha), str(tipo), float(monto), str(descripcion)))

        mysql.connection.commit()
        cur.close()
        
        

        

        flash('Movimiento registrado exitosamente', 'success')
        return redirect(url_for('movimientos'))
     
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    return render_template('Movimientos.html', fecha_actual=fecha_actual)


@app.route('/edit/<id>')
@is_logged_in
def get_movimiento(id):
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor()
    # Verificar que el movimiento pertenece al usuario actual
    cur.execute('SELECT * FROM movimientos WHERE id = %s AND user_id = %s', (id, user_id))
    data = cur.fetchall()
    cur.close()
    
    if not data:
        flash('No tienes permiso para editar este movimiento', 'danger')
        return redirect(url_for('inicio'))
    
    return render_template('edit-movimientos.html', movimiento=data[0])


@app.route('/update/<id>', methods=['POST'])
@is_logged_in
def update_movimiento(id):
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        fecha = request.form['fecha']
        tipo = request.form['tipo']
        monto = request.form['monto']
        descripcion = request.form.get('descripcion')
        
    cur = mysql.connection.cursor()
    
    # Actualizar solo si el movimiento pertenece al usuario
    cur.execute("""
     UPDATE movimientos
    SET fecha = %s,
        tipo = %s,
        monto = %s,
        descripcion = %s
    WHERE id = %s AND user_id = %s                     
    """, (str(fecha), str(tipo), float(monto), descripcion, id, user_id))
    
    mysql.connection.commit()
    cur.close()
    
    flash('Movimiento actualizado satisfactoriamente', 'success')
    return redirect(url_for('inicio'))


@app.route('/delete/<id>')
@is_logged_in
def delete_movimiento(id):
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor()
    # Eliminar solo si el movimiento pertenece al usuario
    cur.execute('DELETE FROM movimientos WHERE id = %s AND user_id = %s', (id, user_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Movimiento removido satisfactoriamente', 'success')
    return redirect(url_for('inicio'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    user_id = session['user_id']
    
    print("=" * 50)
    print(f"USER ID: {user_id}")
    
    cur.execute("""
        SELECT SUM(monto) as total_amount, tipo 
        FROM movimientos 
        WHERE user_id = %s
        GROUP BY tipo 
        ORDER BY tipo
    """, (user_id,))
    
    results = cur.fetchall()
    print(f"RESULTS FROM DB: {results}")
    
    income_expense = []
    for row in results:
        amount = float(row['total_amount']) if row['total_amount'] else 0
        income_expense.append(amount)
    
    print(f"PROCESSED DATA: {income_expense}")
    print("=" * 50)
    
    cur.close()
    
    return render_template('dashboard.html',
        income_vs_expenses=income_expense
    )


@app.route('/register', methods=['GET', 'POST'])    
def register():
    if 'logged_in' in session:
        flash('Cierra sesión para registrar una nueva cuenta', 'info')
        return redirect(url_for('inicio'))
    
    form = RegistroForm(request.form) 
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        
        try:
            # Verificar si el usuario ya existe
            cur.execute("SELECT * FROM users WHERE username = %s", [username])
            if cur.fetchone():
                flash('El usuario ya existe', 'danger')
                return render_template('register.html', form=form)
            
            # Verificar si el email ya existe
            cur.execute("SELECT * FROM users WHERE email = %s", [email])
            if cur.fetchone():
                flash('El email ya está registrado', 'danger')
                return render_template('register.html', form=form)
            
            # Crear usuario con saldo inicial en 0
            cur.execute("INSERT INTO users(name, email, username, password, saldo_actual) VALUES(%s, %s, %s, %s, %s)", 
                        (name, email, username, password, '0'))
            
            mysql.connection.commit()
            
            flash('¡Te has registrado correctamente! Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Error en el registro: {str(e)}', 'danger')
            return render_template('register.html', form=form)
            
        finally:
            cur.close()
    
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        flash('Ya has iniciado sesión', 'info')
        return redirect(url_for('inicio'))
    
    form = LoginForm(request.form) 
    
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password_candidate = form.password.data
        
        cur = mysql.connection.cursor()
        
        try:
            result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
            
            if result > 0:
                data = cur.fetchone()
                password = data['password']
                
                # Comparar contraseñas
                if sha256_crypt.verify(password_candidate, password):
                    # Contraseña correcta - Guardar datos en sesión
                    session['logged_in'] = True
                    session['username'] = username
                    session['name'] = data['name']
                    session['user_id'] = data['id']
                    
                    flash('Has iniciado sesión correctamente', 'success')
                    return redirect(url_for('inicio'))
                else:
                    error = 'Contraseña incorrecta'
                    return render_template('login.html', form=form, error=error)
            else:
                error = 'Usuario no encontrado'
                return render_template('login.html', form=form, error=error)
                
        except Exception as e:
            error = f'Error en la base de datos: {str(e)}'
            return render_template('login.html', form=form, error=error)
            
        finally:
            cur.close()
    
    return render_template('login.html', form=form)


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Has cerrado sesión', 'success')
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)