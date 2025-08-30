import React from "react";
import { ChevronRight, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface BreadcrumbItem {
  label: string;
  href?: string;
  isActive?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  pathname: string;
  setPathname: (pathname: string) => void;
}

export function Breadcrumb({ items, pathname, setPathname }: BreadcrumbProps) {
  const router = useRouter();

  const handleClick = (href?: string, key?: string) => {
    if (href) {
      router.push(href);
    } else if (key) {
      setPathname(key);
    }
  };

  return (
    <nav className="flex items-center space-x-1 text-sm text-muted-foreground">
      <Button
        variant="ghost"
        size="sm"
        className="h-8 px-2 text-muted-foreground hover:text-foreground"
        onClick={() => handleClick("/dashboard")}
      >
        <Home className="h-4 w-4" />
      </Button>

      {items.map((item, index) => (
        <React.Fragment key={index}>
          <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
          {item.isActive ? (
            <span className="font-medium text-foreground">{item.label}</span>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-muted-foreground hover:text-foreground"
              onClick={() => handleClick(item.href, item.label.toLowerCase().replace(/\s+/g, '-'))}
            >
              {item.label}
            </Button>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}
