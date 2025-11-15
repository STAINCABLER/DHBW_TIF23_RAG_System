export function formatBytes(value: number) {
  if (value === 0) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(value) / Math.log(1024))
  const num = value / Math.pow(1024, i)
  return `${num.toFixed(1)} ${sizes[i]}`
}

export function formatDate(value: string) {
  return new Date(value).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
