import { useEffect, useState } from 'react';
import { fetchTrends } from '../api.js';

export default function Trends() {
  const [trends, setTrends] = useState([]);

  useEffect(() => {
    fetchTrends().then(setTrends);
  }, []);

  return (
    <div>
      <h2>Recent Trade Trends</h2>
      <ul>
        {trends.map((t, idx) => (
          <li key={idx}>{t.timestamp} - {t.symbol} - {t.type}</li>
        ))}
      </ul>
    </div>
  );
}
