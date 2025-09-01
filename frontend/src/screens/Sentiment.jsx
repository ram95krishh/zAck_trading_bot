import { useEffect, useState } from 'react';
import { fetchSentiment } from '../api.js';
import Card from '../components/Card.jsx';

export default function Sentiment() {
  const [stats, setStats] = useState([]);

  useEffect(() => {
    fetchSentiment().then(setStats);
  }, []);

  return (
    <Card>
      <h2>Sentiment Stats</h2>
      <ul>
        {stats.map(s => (
          <li key={s.id}>{s.symbol} ({s.sector}) - {s.sentiment} / {s.trend}</li>
        ))}
      </ul>
    </Card>
  );
}
