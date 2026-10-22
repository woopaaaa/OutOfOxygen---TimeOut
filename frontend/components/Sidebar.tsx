"use client";
// import the link from next.js
import Link from "next/link";
// to know where is current page at
import { usePathname } from "next/navigation";

// four screen page sidebars, for the href: , it will pass to next.js
const menuItems = [
  { name: "Factory Health Dashboard", href: "/" },
  { name: "Inventory Intelligence", href: "/inventory" },
  { name: "Smart Production Planner", href: "/planner" },
  { name: "Impact Simulator", href: "/simulator" },
];

export default function Sidebar() {

  const currentPath = usePathname(); //ask the next.js for current address 

  return (
    <nav className="bg-[url('/sidebarbg.jpg')] bg-cover bg-center border-b md:border-b-0 md:border-r border-slate-200 md:w-64 p-4">

      <ul className="flex flex-row md:flex-col gap-2 overflow-x-auto">
        {/* loops each menuItems list to create the buttons */}
        {menuItems.map((item) => {
          // check which page is chosen now
          const isActive = currentPath === item.href;

          return (
            // createthe button in html
            <li key={item.href}>
              <Link
                href={item.href}
                // make the bg color change for the current page 
                className={
                  isActive
                    ? "block rounded-lg px-4 py-2 bg-emerald-600 text-white font-semibold whitespace-nowrap" //when active
                    : "block rounded-lg px-4 py-2 text-slate-700 hover:bg-slate-100 whitespace-nowrap" //when not active
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
