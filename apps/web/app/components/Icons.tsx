type IconProps = { name: string; size?: number };

export function Icon({ name, size = 18 }: IconProps) {
  const paths: Record<string, React.ReactNode> = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></>,
    holdings: <><path d="M4 7h16M4 12h16M4 17h16"/><circle cx="7" cy="7" r="1"/><circle cx="7" cy="12" r="1"/><circle cx="7" cy="17" r="1"/></>,
    scenario: <><path d="M4 19V5M4 19h16"/><path d="m7 15 4-5 3 2 5-7"/></>,
    research: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4M8 11h6M11 8v6"/></>,
    copilot: <><path d="M8 3h8l5 5v8l-5 5H8l-5-5V8z"/><path d="M8 12h.01M12 12h.01M16 12h.01M8 16h8"/></>,
    download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 21h14"/></>,
    chevron: <path d="m8 10 4 4 4-4"/>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    shield: <><path d="M12 3 5 6v5c0 4.5 2.8 8.1 7 10 4.2-1.9 7-5.5 7-10V6z"/><path d="m9 12 2 2 4-5"/></>,
    arrow: <path d="m5 12 14 0m-5-5 5 5-5 5"/>,
    plus: <path d="M12 5v14M5 12h14"/>,
    upload: <><path d="M12 16V4m0 0L8 8m4-4 4 4"/><path d="M4 15v5h16v-5"/></>,
    refresh: <><path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M6.1 8a7 7 0 0 1 11.5-2L20 8M4 16l2.4 2a7 7 0 0 0 11.5-2"/></>,
    alert: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>,
    eye: <><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12"/><circle cx="12" cy="12" r="2.5"/></>,
  };
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name] ?? paths.overview}
    </svg>
  );
}
