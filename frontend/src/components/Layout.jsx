import { useEffect, useState } from 'react';

export default function Layout({ screen, setScreen, children }) {
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark');

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  return (
    <div>
      <nav className="navbar">
        <div className="nav-buttons">
          <button onClick={() => setScreen('positions')} className={screen === 'positions' ? 'active' : ''}>Positions</button>
          <button onClick={() => setScreen('pnl')} className={screen === 'pnl' ? 'active' : ''}>P&amp;L</button>
          <button onClick={() => setScreen('trends')} className={screen === 'trends' ? 'active' : ''}>Trends</button>
          <button onClick={() => setScreen('sentiment')} className={screen === 'sentiment' ? 'active' : ''}>Sentiment</button>
        </div>
        <button className="theme-toggle" onClick={() => setDark(d => !d)}>
          {dark ? 'Light' : 'Dark'}
        </button>
      </nav>
      <main className="container">{children}</main>
    </div>
  );
}
