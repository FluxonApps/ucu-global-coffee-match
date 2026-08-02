import type { PropsWithChildren } from 'react';

const MainLayout = ({ children }: PropsWithChildren) => (
  <div className="h-full bg-[radial-gradient(at_left_top,#050311_20%,#2A53C7_100%)]">{children}</div>
);

export default MainLayout;
