import { useEffect, useState } from 'react';
import { fetchPositions, fetchTotalPnL } from '../api.js';
import Card from '../components/Card.jsx';
import Table from '../components/Table.jsx';

export default function Positions() {
  const [positions, setPositions] = useState([]);
  const [totalPnl, setTotalPnl] = useState(0);

  useEffect(() => {
    fetchPositions().then(setPositions);
    fetchTotalPnL().then(res => setTotalPnl(res.pnl));
  }, []);

  const totalValue = positions.reduce((sum, p) => sum + p.quantity * p.avg_price, 0);
  const pnlColor = totalPnl >= 0 ? 'var(--color-profit)' : 'var(--color-loss)';

  const rows = positions.map(p => [p.symbol, p.quantity, p.avg_price]);

  return (
    <Card>
      <h2>Positions</h2>
      <div className="totals">
        <span>Total Value: {totalValue.toFixed(2)}</span>
        <span style={{ color: pnlColor }}>Total P&amp;L: {totalPnl.toFixed(2)}</span>
      </div>
      <Table headers={['Symbol', 'Qty', 'Avg Price']} rows={rows} />
    </Card>
  );
}
