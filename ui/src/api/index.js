// src/utils/api.js
const API_BASE_URL = "http://localhost:8081";

export async function fetchContainers() {
  const response = await fetch(`${API_BASE_URL}/containers`);
  if (!response.ok) {
    throw new Error("Failed to fetch containers");
  }
  return response.json();
}

export async function fetchContainerInfo(containerId) {
  const response = await fetch(
    `${API_BASE_URL}/containers/${containerId}/info`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch container ${containerId}`);
  }
  return response.json();
}

export async function fetchContainerHistory(containerId, limit = 10) {
  const response = await fetch(
    `${API_BASE_URL}/containers/${containerId}/history?limit=${limit}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch history for ${containerId}`);
  }
  return response.json();
}
