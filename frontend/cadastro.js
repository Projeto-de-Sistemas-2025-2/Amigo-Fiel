document.getElementById('cadastroForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const nome = document.getElementById('nome').value;
  const email = document.getElementById('email').value;
  const senha = document.getElementById('senha').value;
  const confirmar = document.getElementById('confirmar').value;
  const errorDiv = document.getElementById('error');
  errorDiv.style.display = 'none';
  errorDiv.textContent = '';

  if (senha !== confirmar) {
    errorDiv.textContent = 'As senhas não coincidem';
    errorDiv.style.display = 'block';
    return;
  }

  try {
    const response = await fetch('http://localhost:5000/cadastro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome, email, senha })
    });
    if (!response.ok) throw new Error('Erro no cadastro');
    // Sucesso: redirecionar ou mostrar mensagem
    alert('Cadastro realizado com sucesso!');
    // window.location.href = '/login.html';
  } catch (e) {
    errorDiv.textContent = 'Erro ao cadastrar. Tente novamente.';
    errorDiv.style.display = 'block';
  }
});
