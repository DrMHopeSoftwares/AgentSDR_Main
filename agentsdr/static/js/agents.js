async function renameAgent(orgSlug, agentId) {
  const newName = prompt('New agent name:');
  if (!newName) return;
  const resp = await fetch(`/orgs/${orgSlug}/agents/${agentId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName })
  });
  const data = await resp.json();
  if (data.success) window.location.reload();
  else alert(data.error || 'Failed to rename agent');
}

async function deleteAgent(orgSlug, agentId) {
  if (!confirm('Delete this agent? This cannot be undone.')) return;
  const resp = await fetch(`/orgs/${orgSlug}/agents/${agentId}`, { method: 'DELETE' });
  const data = await resp.json();
  if (data.success) window.location.reload();
  else alert(data.error || 'Failed to delete agent');
}

