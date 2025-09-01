import { useEffect, useState } from 'react';
import { fetchDailyPnL, fetchTotalPnL } from '../api.js';
import Card from '../components/Card.jsx';

export default function PnL() {
  const [daily, setDaily] = useState(null);
  const [total, setTotal] = useState(null);

  useEffect(() => {
    fetchDailyPnL().then(setDaily);
    fetchTotalPnL().then(setTotal);
  }, []);

  return (
    <Card>
      <h2>P&amp;L</h2>
      {daily && <p>Daily: {daily.pnl}</p>}
      {total && <p>Total: {total.pnl}</p>}
    </Card>
  );
}
