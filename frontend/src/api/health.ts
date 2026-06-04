export type HealthStatus = {
  status: string;
  service: string;
};

export async function fetchHealth(url: string): Promise<HealthStatus> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }
  return response.json();
}
