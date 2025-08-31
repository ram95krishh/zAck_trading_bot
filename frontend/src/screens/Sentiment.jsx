import { useEffect, useState } from 'react';
import { fetchSentiment } from '../api.js';

export default function Sentiment() {
  const [stats, setStats] = useState([]);

  useEffect(() => {
    fetchSentiment().then(setStats);
  }, []);

  return (
    <div>
      <h2>Sentiment Stats</h2>
      <ul>
        {stats.map(s => (
          <li key={s.id}>{s.symbol} ({s.sector}) - {s.sentiment} / {s.trend}</li>
        ))}
      </ul>
    </div>
  );
}
