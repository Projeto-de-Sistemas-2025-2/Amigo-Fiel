import pyodbc

# Configuração da conexão
conn_str = (
	'DRIVER={SQL Server};'
	'SERVER=localhost;'
	'DATABASE=AmigoFiel;'
	'Trusted_Connection=yes;'
)

def get_connection():
	return pyodbc.connect(conn_str)

# CREATE
def criar_usuario(nome, email, senha, tipo, telefone=None):
	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute('''
		INSERT INTO Usuarios (nome, email, senha, tipo, telefone)
		VALUES (?, ?, ?, ?, ?)
	''', (nome, email, senha, tipo, telefone))
	conn.commit()
	cursor.close()
	conn.close()

# READ (listar todos)
def listar_usuarios():
	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute('SELECT id, nome, email, tipo, telefone, data_cadastro FROM Usuarios')
	usuarios = cursor.fetchall()
	cursor.close()
	conn.close()
	return usuarios

# READ (buscar por id)
def buscar_usuario(id):
	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute('SELECT id, nome, email, tipo, telefone, data_cadastro FROM Usuarios WHERE id = ?', (id,))
	usuario = cursor.fetchone()
	cursor.close()
	conn.close()
	return usuario

# UPDATE
def atualizar_usuario(id, nome=None, email=None, senha=None, tipo=None, telefone=None):
	conn = get_connection()
	cursor = conn.cursor()
	campos = []
	valores = []
	if nome:
		campos.append('nome = ?')
		valores.append(nome)
	if email:
		campos.append('email = ?')
		valores.append(email)
	if senha:
		campos.append('senha = ?')
		valores.append(senha)
	if tipo:
		campos.append('tipo = ?')
		valores.append(tipo)
	if telefone:
		campos.append('telefone = ?')
		valores.append(telefone)
	if not campos:
		return  # Nada para atualizar
	valores.append(id)
	sql = f"UPDATE Usuarios SET {', '.join(campos)} WHERE id = ?"
	cursor.execute(sql, valores)
	conn.commit()
	cursor.close()
	conn.close()

# DELETE
def deletar_usuario(id):
	conn = get_connection()
	cursor = conn.cursor()
	cursor.execute('DELETE FROM Usuarios WHERE id = ?', (id,))
	conn.commit()
	cursor.close()
	conn.close()
 