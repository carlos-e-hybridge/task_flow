import sqlite3
from .modelos import Tarea, Proyecto
import os

DATABASE_NAME = 'tareas.db'


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def crear_tablas():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            fecha_inicio TEXT,
            estado TEXT
        )
    """)

    # Tabla tareas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            fecha_creacion TEXT,
            fecha_limite TEXT,
            prioridad TEXT,
            estado TEXT,
            proyecto_id INTEGER,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)
        )
    """)

    try:
        cursor.execute(
            "INSERT INTO proyectos (id, nombre, descripcion, estado) VALUES (0, 'Tareas Generales', 'Tareas sin clasificar', 'Activo')")
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()


class DBManager:

    def __init__(self):
        crear_tablas()

    def crear_tarea(self, tarea: Tarea) -> Tarea:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tareas(titulo, descripcion, fecha_creacion, fecha_limite, prioridad, estado, proyecto_id)
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (tarea._titulo, tarea._descripcion, tarea._fecha_creacion, tarea._fecha_limite, tarea._prioridad, tarea._estado, tarea._proyecto_id)
        )
        tarea.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return tarea

    def crear_proyecto(self, proyecto: Proyecto) -> Proyecto:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_inicio, estado) VALUES (?, ?, ?, ?)",
            (proyecto._nombre, proyecto._descripcion, proyecto._fecha_inicio, proyecto._estado)
        )
        proyecto.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return proyecto

    def obtener_proyectos(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proyectos")
        filas = cursor.fetchall()

        conn.close()

        proyectos = [
            Proyecto(nombre=fila['nombre'], descripcion=fila['descripcion'],
                     id=fila['id'], estado=fila['estado'])
            for fila in filas
        ]
        return proyectos

    def obtener_proyecto(self, proyecto_id: int):
        conn = get_connection()
        fila = conn.execute(
            "SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)
        ).fetchone()
        conn.close()
        if fila is None:
            return None
        return Proyecto(
            nombre=fila['nombre'], descripcion=fila['descripcion'],
            id=fila['id'], estado=fila['estado']
        )

    def actualizar_proyecto(self, proyecto: Proyecto) -> bool:
        conn = get_connection()
        cursor = conn.execute(
            "UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?",
            (proyecto._nombre, proyecto._descripcion, proyecto.id)
        )
        conn.commit()
        actualizado = cursor.rowcount > 0
        conn.close()
        return actualizado

    def eliminar_proyecto(self, proyecto_id: int) -> bool:
        if proyecto_id == 0:
            return False
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tareas SET proyecto_id = 0 WHERE proyecto_id = ?",
            (proyecto_id,)
        )
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        eliminado = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return eliminado

    def obtener_tarea(self, tarea_id: int):
        conn = get_connection()
        fila = conn.execute(
            "SELECT * FROM tareas WHERE id = ?", (tarea_id,)
        ).fetchone()
        conn.close()
        if fila is None:
            return None
        return Tarea(
            titulo=fila['titulo'], fecha_limite=fila['fecha_limite'],
            prioridad=fila['prioridad'], proyecto_id=fila['proyecto_id'],
            descripcion=fila['descripcion'], id=fila['id'],
            estado=fila['estado'], fecha_creacion=fila['fecha_creacion']
        )

    def actualizar_tarea(self, tarea: Tarea) -> bool:
        conn = get_connection()
        cursor = conn.execute("""
            UPDATE tareas
            SET titulo = ?, descripcion = ?, fecha_limite = ?, prioridad = ?, proyecto_id = ?
            WHERE id = ?
        """, (
            tarea._titulo, tarea._descripcion, tarea._fecha_limite,
            tarea._prioridad, tarea._proyecto_id, tarea.id
        ))
        conn.commit()
        actualizado = cursor.rowcount > 0
        conn.close()
        return actualizado

    def eliminar_tarea(self, tarea_id: int) -> bool:
        conn = get_connection()
        cursor = conn.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        eliminado = cursor.rowcount > 0
        conn.close()
        return eliminado

    def obtener_tareas(self, estado=None, proyecto_id=None):
        """
        Obtiene tareas de la DB. Aplica un algoritmo de ordenamiento y filtrado.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM tareas"
        params = []

        filtros = []
        if estado:
            filtros.append("estado = ?")
            params.append(estado)
        if proyecto_id is not None:
            filtros.append("proyecto_id = ?")
            params.append(proyecto_id)
        if filtros:
            sql += " WHERE " + " AND ".join(filtros)

        sql += " ORDER BY fecha_limite ASC"

        cursor.execute(sql, params)
        filas = cursor.fetchall()
        conn.close()
        
        # Convertimos filas SQL (diccionarios gracias a row_factory) a objetos Tarea (POO)
        tareas = []
        for fila in filas:
            # Recreamos el objeto Tarea a partir de los datos de la DB
            t = Tarea(
                titulo=fila['titulo'], 
                fecha_limite=fila['fecha_limite'],
                prioridad=fila['prioridad'],
                proyecto_id=fila['proyecto_id'],
                descripcion=fila['descripcion'],
                id=fila['id'],
                estado=fila['estado']
            )
            tareas.append(t)
        return tareas


if __name__ == '__main__':
    # Bloque de prueba para la clase
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Base de datos {DATABASE_NAME} eliminada.")

    crear_tablas()
    print(
        f"Base de datos {DATABASE_NAME} y tablas inicializadas correctamente.")

    # Prueba del CRUD (CREATE)
    manager = DBManager()
    tarea_prueba = Tarea(
        titulo="Completar Ejercicio de CRUD",
        fecha_limite="2025-10-30",
        prioridad="Alta",
        proyecto_id=0,
        descripcion="Implementar el módulo database.py"
    )

    tarea_creada = manager.crear_tarea(tarea_prueba)
    print(f"Tarea creada y ID asignado: {tarea_creada.id}")