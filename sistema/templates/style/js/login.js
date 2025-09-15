document.getElementById('loginBtn').addEventListener('click', async function() {
  const email = document.getElementById('email').value;
  const senha = document.getElementById('senha').value;
  const errorDiv = document.getElementById('error');
  errorDiv.style.display = 'none';
  errorDiv.textContent = '';

  try {
    const response = await fetch('http://localhost:5000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    });
    if (!response.ok) throw new Error('Login inválido');
    // Sucesso: redirecionar ou salvar token
    // window.location.href = '/dashboard';
  } catch (e) {
    errorDiv.textContent = 'E-mail ou senha incorretos';
    errorDiv.style.display = 'block';
  }
});

// adicionar eventos para "Esqueceu sua senha?" e "Cadastre-se"
document.getElementById('forgotBtn').addEventListener('click', function() {
  alert('Função de recuperação de senha não implementada.');
});