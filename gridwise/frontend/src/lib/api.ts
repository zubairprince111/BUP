import { OptimizationRequest, OptimizationResponse } from '../types';

const BASE_URLS = [
  import.meta.env.VITE_API_BASE_URL || '',
  'http://127.0.0.1:8000',
  'http://localhost:8000',
].filter((url, idx, self) => self.indexOf(url) === idx);

export async function checkHealth(): Promise<{ status: string }> {
  let lastError: any = null;
  for (const baseUrl of BASE_URLS) {
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      lastError = err;
    }
  }
  throw lastError || new Error('Health check failed across all endpoints');
}

export async function optimizeEnergy(
  request: OptimizationRequest
): Promise<OptimizationResponse> {
  let lastErrorMsg = 'Network request failed';
  for (const baseUrl of BASE_URLS) {
    try {
      const response = await fetch(`${baseUrl}/optimize-energy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        return await response.json();
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Optimization request failed' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
    } catch (err: any) {
      lastErrorMsg = err.message || 'Optimization call failed';
      if (err.message && (err.message.includes('HTTP ') || err.message.includes('Invalid') || err.message.includes('infeasible') || err.message.includes('failed'))) {
        throw err;
      }
    }
  }
  throw new Error(lastErrorMsg);
}

