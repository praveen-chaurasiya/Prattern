interface StaleBannerProps {
  scanDate: string;
}

export function StaleBanner({ scanDate }: StaleBannerProps) {
  return (
    <div className="bg-danger/15 border-b border-danger/30 px-4 py-2 text-center text-sm text-danger">
      Data is stale — last scan: {scanDate}. Run the scanner to refresh.
    </div>
  );
}
