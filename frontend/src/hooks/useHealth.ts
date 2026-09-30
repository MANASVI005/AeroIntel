import { usePolling } from './useApi';
import { api } from '../services/api';
import type { HealthResponse } from '../services/types';

/**
 * Polls GET /health every 30 s (as per spec) and exposes the health payload.
 * The AppShell status dot and Settings → System Status card consume this.
 */
export function useHealth(): {
  health: HealthResponse | null;
  online: boolean;
  dbConnected: boolean;
} {
  const { data } = usePolling<HealthResponse>(() => api.getHealth(), 30000);
  const online = data?.status === 'healthy';
  const dbConnected = data?.database === 'connected';
  return { health: data, online, dbConnected };
}
