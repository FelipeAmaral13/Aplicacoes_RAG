-- Cria uma tabela confidencial
CREATE TABLE salarios_confidenciais (
    id SERIAL PRIMARY KEY,
    funcionario VARCHAR(100),
    salario DECIMAL(10,2),
    conta_bancaria VARCHAR(50)
);

INSERT INTO salarios_confidenciais (funcionario, salario, conta_bancaria) VALUES 
('Felipe CEO', 50000.00, 'BR-12345'),
('Ze CFO', 45000.00, 'BR-67890');

-- A VULNERABILIDADE:
-- Concedendo acesso total a qualquer usuário (incidente de permissão excessiva)
GRANT ALL PRIVILEGES ON TABLE salarios_confidenciais TO PUBLIC;