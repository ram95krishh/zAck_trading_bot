import { useState } from 'react';
import Positions from './screens/Positions.jsx';
import PnL from './screens/PnL.jsx';
import Trends from './screens/Trends.jsx';
import Sentiment from './screens/Sentiment.jsx';
import './app.css';

export default function App() {
  const [screen, setScreen] = useState('positions');

  const renderScreen = () => {
    switch (screen) {
      case 'pnl':
        return <PnL />;
      case 'trends':
        return <Trends />;
      case 'sentiment':
        return <Sentiment />;
      default:
        return <Positions />;
    }
  };

  return (
    <div>
      <nav>
        <button onClick={() => setScreen('positions')}>Positions</button>
        <button onClick={() => setScreen('pnl')}>P&amp;L</button>
        <button onClick={() => setScreen('trends')}>Trends</button>
        <button onClick={() => setScreen('sentiment')}>Sentiment</button>
      </nav>
      {renderScreen()}
    </div>
  );
}
