import { useEffect, useState } from 'react';
import { fetchDailyPnL, fetchTotalPnL } from '../api.js';

export default function PnL() {
  const [daily, setDaily] = useState(null);
  const [total, setTotal] = useState(null);

  useEffect(() => {
    fetchDailyPnL().then(setDaily);
    fetchTotalPnL().then(setTotal);
  }, []);

  return (
    <div>
      <h2>P&amp;L</h2>
      {daily && <p>Daily: {daily.pnl}</p>}
      {total && <p>Total: {total.pnl}</p>}
    </div>
  );
}
