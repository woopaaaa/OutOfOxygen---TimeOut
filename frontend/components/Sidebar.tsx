"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// four screen page sidebars 
const menuItems = [
  { name: "Factory Health Dashboard", href: "/" },
  { name: "Inventory Intelligence", href: "/inventory" },
  { name: "Smart Production Planner", href: "/planner" },
  { name: "Impact Simulator", href: "/simulator" },
];

export default function Sidebar() {

  const currentPath = usePathname(); //ask the next.js for current address and store it

  return (
    <nav className="bg-white border-b md:border-b-0 md:border-r border-slate-200 md:w-64 p-4">
      <ul className="flex flex-row md:flex-col gap-2 overflow-x-auto">
        {/* make one link per item */}
        {menuItems.map((item) => {
          const isActive = currentPath === item.href;

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={
                  isActive
                    ? "block rounded-lg px-4 py-2 bg-emerald-600 text-white font-semibold whitespace-nowrap"
                    : "block rounded-lg px-4 py-2 text-slate-700 hover:bg-slate-100 whitespace-nowrap"
                }
              >
                {item.name}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
