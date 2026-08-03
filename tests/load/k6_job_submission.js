import http from 'k6/http';
import { check, sleep } from 'k6';
import ws from 'k6/ws';

export const options = {
  stages: [
    { duration: '1m', target: 20 },  // ramp up to 20 users
    { duration: '3m', target: 100 }, // ramp up to 100 users (NFR-PERF-03)
    { duration: '1m', target: 0 },   // ramp down
  ],
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
const MOCK_TOKEN = __ENV.AUTH_TOKEN || 'mock-token';

export default function () {
  const params = {
    headers: {
      'Authorization': `Bearer ${MOCK_TOKEN}`,
      'x-workspace-id': '1',
      'Content-Type': 'application/x-www-form-urlencoded'
    },
  };

  // 1. Submit a job
  const payload = {
    arxiv_id: '2103.00020'
  };

  const res = http.post(`${BASE_URL}/jobs`, payload, params);

  check(res, {
    'job created successfully': (r) => r.status === 201,
  });

  if (res.status === 201) {
    const jobId = res.json('id');

    // 2. Connect to WebSocket
    const wsUrl = `ws://${BASE_URL.replace(/^http:\/\//, '')}/ws/${jobId}`;
    const wsRes = ws.connect(wsUrl, params, function (socket) {
      socket.on('open', () => {
        // Wait 10 seconds to receive some events
        socket.setTimeout(function () {
          socket.close();
        }, 10000);
      });

      socket.on('message', (data) => {
        // Just verify we get valid JSON payload
        const msg = JSON.parse(data);
        check(msg, {
          'received valid ws event': (m) => m.event_type !== undefined,
        });
      });
    });

    check(wsRes, { 'websocket connected successfully': (r) => r && r.status === 101 });
  }

  sleep(1);
}
