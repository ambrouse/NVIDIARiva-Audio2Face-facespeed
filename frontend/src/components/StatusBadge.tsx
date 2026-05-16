type StatusBadgeProps = {
  healthy: boolean;
  label: string;
};

export function StatusBadge({ healthy, label }: StatusBadgeProps) {
  return <span className={healthy ? 'badge badgeOk' : 'badge badgeWarn'}>{label}</span>;
}
