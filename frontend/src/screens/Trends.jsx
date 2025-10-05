import { useEffect, useState } from 'react';
import { fetchTrends } from '../api.js';
import Card from '../components/Card.jsx';

export default function Trends() {
  const [trends, setTrends] = useState([]);

  useEffect(() => {
    fetchTrends().then(setTrends);
  }, []);

  return (
    <Card>
      <h2>Recent Trade Trends</h2>
      <ul>
        {trends.map((t, idx) => (
          <li key={idx}>{t.timestamp} - {t.symbol} - {t.type}</li>
        ))}
      </ul>
    </Card>
  );
}
