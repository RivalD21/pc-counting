export function WsImageStream({
  gambar,
  status,
}: {
  gambar?: string;
  status?: string;
}) {
  return (
    <div>
      <img
        src={gambar}
        alt="stream"
        className="rounded-xl bg-black"
        width={640}
        height={480}
      />
      <div className="absolute top-2 left-2 px-2 py-1 rounded-md text-xs font-medium text-white bg-black/50">
        {status}
      </div>
    </div>
  );
}
