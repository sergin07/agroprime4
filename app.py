from flask import Flask, redirect, url_for, render_template

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

@app.route("/reportes/<string:id>/")
def reportes_id(id):
    return render_template('reportes.html', id=id)

if __name__ == '__main__':
    app.run(debug=True)