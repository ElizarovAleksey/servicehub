const themeBtn = document.getElementById('toggleTheme');
  const html = document.documentElement;

  themeBtn.onclick = () => {
    html.classList.toggle('dark');
    localStorage.setItem('theme',
      html.classList.contains('dark') ? 'dark' : 'light');
  };

  if (localStorage.getItem('theme') === 'dark') {
    html.classList.add('dark');
  }