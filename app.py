from flask import Flask, abort, redirect, render_template, request, url_for
from src.modelos import Tarea, Proyecto
from src.database import DBManager

app = Flask(__name__)
db_manager = DBManager()

@app.route('/')
def index():
    tareas_pendientes = db_manager.obtener_tareas(estado="Pendiente")
    proyectos = db_manager.obtener_proyectos()
    return render_template(
        'index.html',
        tareas=_preparar_tareas(tareas_pendientes, proyectos),
        proyectos=[proyecto.to_dict() for proyecto in proyectos],
        proyecto_actual=None
    )


def _preparar_tareas(tareas, proyectos):
    nombres_proyectos = {proyecto.id: proyecto._nombre for proyecto in proyectos}
    tareas_dict = [tarea.to_dict() for tarea in tareas]
    for tarea in tareas_dict:
        tarea['proyecto_nombre'] = nombres_proyectos.get(tarea['proyecto_id'], 'Sin proyecto')
    return tareas_dict


@app.route('/crear', methods=['GET', 'POST'])
def crear_tarea_web():
    proyectos = db_manager.obtener_proyectos()

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        limite = request.form.get('fecha_limite', '')
        prioridad = request.form.get('prioridad', '')
        try:
            proyecto_id = int(request.form.get('proyecto_id', ''))
        except ValueError:
            abort(400)
        if not titulo or not limite or prioridad not in {'Alta', 'Media', 'Baja'}:
            abort(400)
        if db_manager.obtener_proyecto(proyecto_id) is None:
            abort(400)

        nueva_tarea = Tarea(
            titulo=titulo, descripcion=descripcion, fecha_limite=limite, prioridad=prioridad, proyecto_id=proyecto_id
        )

        db_manager.crear_tarea(nueva_tarea)

        return redirect(url_for('index'))

    return render_template(
        'formulario_tarea.html',
        proyectos=[proyecto.to_dict() for proyecto in proyectos],
        tarea=None
    )


@app.route('/proyectos/crear', methods=['GET', 'POST'])
def crear_proyecto_web():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        if not nombre:
            abort(400)
        proyecto = db_manager.crear_proyecto(Proyecto(nombre=nombre, descripcion=descripcion))
        return redirect(url_for('ver_proyecto', proyecto_id=proyecto.id))
    proyectos = db_manager.obtener_proyectos()
    return render_template(
        'formulario_proyecto.html',
        proyecto=None,
        proyecto_actual=None,
        proyectos=[item.to_dict() for item in proyectos]
    )


@app.route('/proyectos/<int:proyecto_id>')
def ver_proyecto(proyecto_id):
    proyecto = db_manager.obtener_proyecto(proyecto_id)
    if proyecto is None:
        abort(404)
    proyectos = db_manager.obtener_proyectos()
    tareas = db_manager.obtener_tareas(estado='Pendiente', proyecto_id=proyecto_id)
    return render_template(
        'index.html',
        proyecto=proyecto.to_dict(),
        proyecto_actual=proyecto.to_dict(),
        tareas=_preparar_tareas(tareas, proyectos),
        proyectos=[item.to_dict() for item in proyectos]
    )


@app.route('/proyectos/<int:proyecto_id>/editar', methods=['GET', 'POST'])
def editar_proyecto_web(proyecto_id):
    proyecto = db_manager.obtener_proyecto(proyecto_id)
    if proyecto is None:
        abort(404)
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        if not nombre:
            abort(400)
        proyecto = Proyecto(nombre=nombre, descripcion=descripcion, id=proyecto_id)
        if not db_manager.actualizar_proyecto(proyecto):
            abort(404)
        return redirect(url_for('ver_proyecto', proyecto_id=proyecto_id))
    proyectos = db_manager.obtener_proyectos()
    proyecto_dict = proyecto.to_dict()
    return render_template(
        'formulario_proyecto.html',
        proyecto=proyecto_dict,
        proyecto_actual=proyecto_dict,
        proyectos=[item.to_dict() for item in proyectos]
    )


@app.route('/proyectos/<int:proyecto_id>/eliminar', methods=['POST'])
def eliminar_proyecto_web(proyecto_id):
    if not db_manager.eliminar_proyecto(proyecto_id):
        abort(404 if proyecto_id != 0 else 400)
    return redirect(url_for('index'))


@app.route('/tareas/<int:tarea_id>/editar', methods=['GET', 'POST'])
def editar_tarea_web(tarea_id):
    tarea = db_manager.obtener_tarea(tarea_id)
    if tarea is None:
        abort(404)
    proyectos = db_manager.obtener_proyectos()
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_limite = request.form.get('fecha_limite', '')
        prioridad = request.form.get('prioridad', '')
        try:
            proyecto_id = int(request.form.get('proyecto_id', ''))
        except ValueError:
            abort(400)
        if not titulo or not fecha_limite or prioridad not in {'Alta', 'Media', 'Baja'}:
            abort(400)
        if db_manager.obtener_proyecto(proyecto_id) is None:
            abort(400)
        tarea = Tarea(
            titulo=titulo, descripcion=descripcion, fecha_limite=fecha_limite,
            prioridad=prioridad, proyecto_id=proyecto_id, id=tarea_id,
            estado=tarea._estado
        )
        if not db_manager.actualizar_tarea(tarea):
            abort(404)
        return _redirigir_a_proyecto(request.form.get('return_project_id'))
    return render_template(
        'formulario_tarea.html',
        proyectos=[proyecto.to_dict() for proyecto in proyectos],
        tarea=tarea.to_dict(),
        return_project_id=request.args.get('proyecto_id', type=int)
    )


@app.route('/tareas/<int:tarea_id>/eliminar', methods=['POST'])
def eliminar_tarea_web(tarea_id):
    if not db_manager.eliminar_tarea(tarea_id):
        abort(404)
    return _redirigir_a_proyecto(request.form.get('return_project_id'))


def _redirigir_a_proyecto(proyecto_id):
    try:
        proyecto_id = int(proyecto_id)
    except (TypeError, ValueError):
        return redirect(url_for('index'))
    if db_manager.obtener_proyecto(proyecto_id) is None:
        return redirect(url_for('index'))
    return redirect(url_for('ver_proyecto', proyecto_id=proyecto_id))

if __name__ == '__main__':
    print('Iniciando servidor Flask')
    app.run(debug=True)