import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Warehouse,
  Users,
  Truck,
  DollarSign,
  BarChart2,
  Settings,
  TrendingUp,
  TrendingDown,
  FileText,
  Activity,
  X,
  ChevronDown,
  ClipboardList,
  Receipt,
  BookOpen,
  CreditCard,
  Layers,
  ArrowLeftRight,
  FilePlus2,
  ShoppingBag,
  ScrollText,
} from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { hasCapability, type AppCapability } from '../lib/permissions';

interface NavChild {
  to: string;
  label: string;
}

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
  capability?: AppCapability;
  children?: NavChild[];
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true, capability: 'dashboard:view' },
  {
    to: '/sales', label: 'Sales', icon: TrendingUp, capability: 'sales:view',
    children: [
      { to: '/sales', label: 'Invoices' },
      { to: '/sales/orders', label: 'Sales Orders' },
      { to: '/sales/quotations', label: 'Quotations' },
    ],
  },
  {
    to: '/purchases', label: 'Purchases', icon: TrendingDown, capability: 'purchases:view',
    children: [
      { to: '/purchases', label: 'Invoices' },
      { to: '/purchases/orders', label: 'Purchase Orders' },
      { to: '/purchases/requisitions', label: 'Requisitions' },
      { to: '/purchases/rfqs', label: 'Supplier Quotations' },
    ],
  },
  {
    to: '/inventory', label: 'Inventory', icon: Warehouse, capability: 'inventory:view',
    children: [
      { to: '/inventory', label: 'Items & Stock' },
      { to: '/inventory/bundles', label: 'Bundles' },
      { to: '/inventory/warehouse', label: 'Warehouse Stock' },
      { to: '/inventory/movements', label: 'Stock Movements' },
    ],
  },
  { to: '/customers', label: 'Customers', icon: Users, capability: 'customers:view' },
  { to: '/suppliers', label: 'Suppliers', icon: Truck, capability: 'suppliers:view' },
  {
    to: '/finance', label: 'Finance', icon: DollarSign, capability: 'finance:view',
    children: [
      { to: '/finance', label: 'Overview' },
      { to: '/finance/payments', label: 'Payments' },
      { to: '/finance/journals', label: 'Journal Entries' },
    ],
  },
  { to: '/operations', label: 'Operations', icon: Activity, capability: 'operations:view' },
  { to: '/reports', label: 'Reports', icon: BarChart2, capability: 'reports:view' },
];

const bottomItems: NavItem[] = [
  { to: '/settings', label: 'Settings', icon: Settings, capability: 'settings:view' },
];

interface SidebarProps {
  mobile?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ mobile = false, onClose }: SidebarProps) {
  const location = useLocation();
  const roles = useAuthStore((s) => s.roles);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleExpand = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const isParentActive = (item: NavItem) => {
    if (item.exact) return location.pathname === item.to;
    return location.pathname === item.to || location.pathname.startsWith(item.to + '/');
  };

  const isChildActive = (child: NavChild, parent: NavItem) => {
    // For exact parent path children (e.g., /sales -> Invoices), match exactly
    if (child.to === parent.to) {
      return location.pathname === child.to;
    }
    return location.pathname === child.to || location.pathname.startsWith(child.to + '/');
  };

  const isOpen = (item: NavItem) => expanded[item.to] ?? isParentActive(item);

  const renderItem = (item: NavItem) => {
    // Check capability-based access
    if (item.capability && roles.length > 0 && !hasCapability(roles, item.capability)) {
      return null;
    }

    const active = isParentActive(item);

    if (item.children) {
      const open = isOpen(item);
      return (
        <div key={item.to}>
          <button
            onClick={() => toggleExpand(item.to)}
            className={`sidebar-link w-full justify-between ${active ? 'active' : ''}`}
          >
            <span className="flex items-center gap-3">
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </span>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
          </button>
          {open && (
            <div className="ml-8 mt-0.5 space-y-0.5 border-l-2 border-gray-100 dark:border-slate-700 pl-3">
              {item.children.map((child) => (
                <NavLink
                  key={child.to}
                  to={child.to}
                  end={child.to === item.to}
                  className={`block px-3 py-1.5 text-sm rounded-md transition-colors ${
                    isChildActive(child, item)
                      ? 'text-brand-700 dark:text-brand-300 bg-brand-50 dark:bg-slate-800 font-medium'
                      : 'text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-slate-800'
                  }`}
                  onClick={mobile ? onClose : undefined}
                >
                  {child.label}
                </NavLink>
              ))}
            </div>
          )}
        </div>
      );
    }

    return (
      <NavLink
        key={item.to}
        to={item.to}
        end={item.exact}
        className={`sidebar-link ${active ? 'active' : ''}`}
        onClick={mobile ? onClose : undefined}
      >
        <item.icon className="w-5 h-5 flex-shrink-0" />
        <span>{item.label}</span>
      </NavLink>
    );
  };

  return (
    <aside
      className={`${
        mobile
          ? 'h-full w-full bg-white dark:bg-slate-900 flex flex-col'
          : 'fixed left-0 top-16 bottom-0 w-[260px] bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-700 z-40 flex flex-col'
      }`}
    >
      {/* Mobile header with close button */}
      {mobile && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-700">
          <span className="text-lg font-bold text-gray-900 dark:text-gray-100">Menu</span>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Main Menu
        </p>
        {navItems.map(renderItem)}

        <div className="my-4 border-t border-gray-100 dark:border-slate-700" />

        <p className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          System
        </p>
        {bottomItems.map(renderItem)}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-100 dark:border-slate-700 pb-safe">
        <div className="flex items-center gap-2 text-xs text-gray-400 dark:text-slate-500">
          <div className="w-2 h-2 bg-green-500 rounded-full" />
          <span>System Online</span>
        </div>
        <p className="text-[10px] text-gray-300 dark:text-slate-600 mt-1">Traders v1.0.0</p>
      </div>
    </aside>
  );
}
