'use client';

interface AgePyramidProps {
  distribution: Record<string, number>;
  minAge?: number;
  maxAge?: number;
}

export function AgePyramid({ distribution, minAge = 18, maxAge = 95 }: AgePyramidProps) {
  const entries = Object.entries(distribution)
    .map(([k, v]) => [Number(k), Number(v)] as [number, number])
    .sort((a, b) => a[0] - b[0]);
  const max = Math.max(...entries.map(([, v]) => v), 1);

  return (
    <div>
      <div className="flex items-end gap-0.5 h-24">
        {entries.map(([age, count]) => {
          const outOfRange = age < minAge || age > maxAge;
          return (
            <div
              key={age}
              className="flex-1 rounded-t-sm"
              style={{
                height: `${Math.max((count / max) * 100, 2)}%`,
                backgroundColor: outOfRange ? '#E24B4A' : '#9164CD',
              }}
              title={`${age} ans : ${count.toLocaleString('fr-FR')}`}
            />
          );
        })}
      </div>
      <div className="flex justify-between mt-2 text-xs">
        <span className="font-bold text-red-600">{'<'} {minAge} ans</span>
        <span className="text-gray-500">{minAge}-{maxAge} ans</span>
        <span className="font-bold text-red-600">{'>'} {maxAge} ans</span>
      </div>
    </div>
  );
}