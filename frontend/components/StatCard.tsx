// for the cards

type StatCardProps = {
  label: string;
  value: string | number;
  note?: string;
};

export default function StatCard({ label, value, note }: StatCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{note}</p>
    </div>
  );
}
