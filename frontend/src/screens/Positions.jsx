import { useEffect, useState } from 'react';
import { fetchPositions } from '../api.js';

export default function Positions() {
  const [positions, setPositions] = useState([]);

  useEffect(() => {
    fetchPositions().then(setPositions);
  }, []);

  return (
    <div>
      <h2>Positions</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Qty</th>
            <th>Avg Price</th>
          </tr>
        </thead>
        <tbody>
          {positions.map(p => (
            <tr key={p.id}>
              <td>{p.symbol}</td>
              <td>{p.quantity}</td>
              <td>{p.avg_price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
