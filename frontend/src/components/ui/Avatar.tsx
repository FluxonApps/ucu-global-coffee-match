const Avatar = ({ src, name, size = 40 }: { src: string; name: string; size?: number }) => (
  <img
    src={src}
    alt={name}
    width={size}
    height={size}
    className="rounded-full object-cover bg-muted flex-shrink-0"
    style={{ width: size, height: size }}
  />
);

export default Avatar;
