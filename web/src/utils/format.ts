export function formatPercent(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
}

export function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`;
}
