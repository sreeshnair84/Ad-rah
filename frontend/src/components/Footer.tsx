export function Footer() {
  return (
    <footer className="w-full bg-background border-t border-border mt-auto">
      <div className="mx-auto max-w-screen-2xl px-3 py-6 text-center">
        <p className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} <span className="relative inline-block">
            <span className="block text-[10px]">Adārah</span>
            <span className="absolute -top-1 -right-0 text-[8px] leading-none text-muted-foreground">from Hebron™</span>
          </span> — Built for Next.js App Router, Tailwind, shadcn/ui.
        </p>
      </div>
    </footer>
  );
}
