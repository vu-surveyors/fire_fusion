import Image from "next/image";
import Link from "next/link";
import { getNavigationForPath } from "@/config/nav";

type SiteHeaderProps = {
  title: string;
  activePath: string;
};

export function SiteHeader({ title, activePath }: SiteHeaderProps) {
  const navigation = getNavigationForPath(activePath);

  return (
    <header className="site-header">
      <div className="site-header-main">
        <Link aria-label="FireFusion overview" className="brand-lockup" href="/">
          <Image
            aria-hidden="true"
            alt=""
            className="brand-mark"
            height={48}
            src="/images/fire-fusion.png"
            width={136}
          />
        </Link>
        <div className="header-page-title">
          <p className="header-kicker">SENSOR-HARMONIZED INTELLIGENCE</p>
          <h1 className="page-title">{title}</h1>
        </div>
        <span className="header-status">
          <span aria-hidden="true" className="status-indicator" />
          DEMO ENVIRONMENT
        </span>
      </div>
      <nav aria-label="Main navigation" className="main-nav">
        {navigation.map((item) => (
          <Link
            aria-current={item.active ? "page" : undefined}
            key={item.href}
            className={`nav-link${item.active ? " active" : ""}`}
            href={item.href}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
