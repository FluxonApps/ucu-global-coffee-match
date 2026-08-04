import { useState } from 'react';

const getInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? '';
  const last = parts.length > 1 ? parts[parts.length - 1][0] : '';
  return (first + last).toUpperCase();
};

const Avatar = ({
  src,
  name,
  size = 40,
}: {
  src?: string;
  name: string;
  size?: number;
}) => {
  const [imageFailed, setImageFailed] = useState(false);

  const showImage = Boolean(src) && !imageFailed;

  if (showImage) {
    return (
      <img
        src={src}
        alt={name}
        width={size}
        height={size}
        className="rounded-full object-cover bg-muted flex-shrink-0"
        style={{ width: size, height: size }}
        onError={() => setImageFailed(true)}
      />
    );
  }

  return (
    <div
      className="rounded-full bg-primary/10 text-primary flex items-center justify-center font-semibold flex-shrink-0"
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {getInitials(name)}
    </div>
  );
};

export default Avatar;