-- Criação do banco de dados
CREATE DATABASE AmigoFiel;
USE AmigoFiel;

-- Tabela de Usuários (ONGs, Protetores, Adotantes)
CREATE TABLE Usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ONG', 'Protetor', 'Adotante')),
    telefone VARCHAR(20),
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Animais
CREATE TABLE Animais (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    raca VARCHAR(50),
    idade INT,
    sexo VARCHAR(10) CHECK (sexo IN ('Macho', 'Fêmea')),
    descricao TEXT,
    status VARCHAR(20) CHECK (status IN ('Disponível', 'Adotado', 'Em tratamento')) DEFAULT 'Disponível',
    usuario_id INT,
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
);

-- Tabela de Adoções
CREATE TABLE Adocoes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    animal_id INT NOT NULL,
    adotante_id INT NOT NULL,
    data_adocao DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('Pendente', 'Aprovada', 'Recusada')) DEFAULT 'Pendente',
    FOREIGN KEY (animal_id) REFERENCES Animais(id),
    FOREIGN KEY (adotante_id) REFERENCES Usuarios(id)
);

-- Tabela de Mensagens (comunicação entre usuários)
CREATE TABLE Mensagens (
    id INT IDENTITY(1,1) PRIMARY KEY,
    remetente_id INT NOT NULL,
    destinatario_id INT NOT NULL,
    mensagem TEXT NOT NULL,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (remetente_id) REFERENCES Usuarios(id),
    FOREIGN KEY (destinatario_id) REFERENCES Usuarios(id)
);