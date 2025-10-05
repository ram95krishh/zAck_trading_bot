import { useState } from 'react';
import Layout from './components/Layout.jsx';
import Positions from './screens/Positions.jsx';
import PnL from './screens/PnL.jsx';
import Trends from './screens/Trends.jsx';
import Sentiment from './screens/Sentiment.jsx';
import './app.css';

export default function App() {
  const [screen, setScreen] = useState('positions');

  let content;
  switch (screen) {
    case 'pnl':
      content = <PnL />;
      break;
    case 'trends':
      content = <Trends />;
      break;
    case 'sentiment':
      content = <Sentiment />;
      break;
    default:
      content = <Positions />;
  }

  return (
    <Layout screen={screen} setScreen={setScreen}>
      {content}
    </Layout>
  );
}
