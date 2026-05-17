import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  DollarSign,
  TrendingUp,
  CreditCard,
  Wallet,
  Package,
  AlertTriangle,
  Users,
  ShoppingCart,
  Plus,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import KPICard from '../components/KPICard';
import { dashboardApi } from '../lib/api';
import { formatCurrency, formatDate, getStatusColor } from '../lib/utils';
import { useCompanyStore } from '../stores/companyStore';

interface DashboardKPIs {
  todays_sales: number;
  monthly_revenue: number;
  outstanding_receivables: number;
  outstanding_payables: number;
  stock_value: number;
  low_stock_items: number;
  total_customers: number;
  total_orders_today: number;
  currency: string;
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [salesTrend, setSalesTrend] = useState<any[]>([]);
  const [topCustomers, setTopCustomers] = useState<any[]>([]);
  const [recentOrders, setRecentOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const companyRevision = useCompanyStore((s) => s.revision);
  const companyInitialized = useCompanyStore((s) => s.initialized);
  const activeCompany = useCompanyStore((s) => s.company);

  useEffect(() => {
    if (!companyInitialized) return;
    void loadDashboard();
  }, [companyRevision, companyInitialized]);

  const loadDashboard = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [kpiRes, trendRes, customersRes, ordersRes] = await Promise.all([
        dashboardApi.getKPIs(),
        dashboardApi.getSalesTrend(),
        dashboardApi.getTopCustomers(8),
        dashboardApi.getRecentOrders(10),
      ]);

      setKpis(kpiRes.data.message);
      setSalesTrend(trendRes.data.message || []);
      setTopCustomers(customersRes.data.message || []);
      setRecentOrders(ordersRes.data.message || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setLoadError('Could not load dashboard data. Check your connection and try again.');
      setKpis(null);
      setSalesTrend([]);
      setTopCustomers([]);
      setRecentOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#be185d', '#65a30d'];

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-gray-500 dark:text-slate-400 mt-1 text-sm">
            Welcome back — here's your business at a glance
            {activeCompany ? ` for ${activeCompany}` : ''}.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 self-start">
          <button type="button" onClick={() => void loadDashboard()} className="btn-secondary flex items-center gap-2 text-sm" disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      {loadError && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-100 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" role="alert">
          <span>{loadError}</span>
          <button type="button" onClick={() => void loadDashboard()} className="btn-primary text-sm shrink-0">
            Retry
          </button>
        </div>
      )}

      {/* Quick actions */}
      <div className="flex flex-wrap gap-2">
        <Link to="/sales/new" className="btn-primary inline-flex items-center gap-2 text-sm">
          <Plus size={14} /> New sales invoice
        </Link>
        <Link to="/sales/orders/new" className="btn-secondary inline-flex items-center gap-2 text-sm">
          <Plus size={14} /> New sales order
        </Link>
        <Link to="/purchases/new" className="btn-secondary inline-flex items-center gap-2 text-sm">
          <Plus size={14} /> New purchase invoice
        </Link>
        <Link to="/inventory/items/new" className="btn-secondary inline-flex items-center gap-2 text-sm">
          <Plus size={14} /> New item
        </Link>
        <Link to="/reports" className="btn-secondary inline-flex items-center gap-2 text-sm">
          Reports
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <KPICard
          title="Today's Sales"
          value={kpis?.todays_sales || 0}
          icon={DollarSign}
          format="currency"
          color="green"
          loading={loading}
        />
        <KPICard
          title="Monthly Revenue"
          value={kpis?.monthly_revenue || 0}
          icon={TrendingUp}
          format="currency"
          color="blue"
          loading={loading}
        />
        <KPICard
          title="Outstanding Receivables"
          value={kpis?.outstanding_receivables || 0}
          icon={CreditCard}
          format="currency"
          color="yellow"
          loading={loading}
        />
        <KPICard
          title="Outstanding Payables"
          value={kpis?.outstanding_payables || 0}
          icon={Wallet}
          format="currency"
          color="red"
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <KPICard
          title="Stock Value"
          value={kpis?.stock_value || 0}
          icon={Package}
          format="currency"
          color="purple"
          loading={loading}
        />
        <KPICard
          title="Low Stock Items"
          value={kpis?.low_stock_items || 0}
          icon={AlertTriangle}
          format="number"
          color="yellow"
          loading={loading}
        />
        <KPICard
          title="Total Customers"
          value={kpis?.total_customers || 0}
          icon={Users}
          format="number"
          color="blue"
          loading={loading}
        />
        <KPICard
          title="Today's Orders"
          value={kpis?.total_orders_today || 0}
          icon={ShoppingCart}
          format="number"
          color="green"
          loading={loading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Sales Trend */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Sales Trend</h3>
            <p className="text-xs sm:text-sm text-gray-500">Monthly revenue for the last 12 months</p>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={salesTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(val) => `${(val / 1000000).toFixed(1)}M`} />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), 'Revenue']}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Bar dataKey="total" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Customers */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Top Customers</h3>
            <p className="text-xs sm:text-sm text-gray-500">By revenue this fiscal year</p>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={topCustomers.slice(0, 6)}
                  dataKey="total_revenue"
                  nameKey="customer_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }) => `${(name || '').slice(0, 10)} (${(percent * 100).toFixed(0)}%)`}
                >
                  {topCustomers.slice(0, 6).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [formatCurrency(value), 'Revenue']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-gray-900">Recent Orders</h3>
            <p className="text-xs sm:text-sm text-gray-500">Latest sales orders</p>
          </div>
        </div>

        {/* Desktop table */}
        <div className="hidden md:block table-container">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Order</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Customer</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Date</th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Amount</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {recentOrders.map((order) => (
                <tr key={order.name} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-3 text-sm font-medium text-brand-700">{order.name}</td>
                  <td className="px-6 py-3 text-sm text-gray-700">{order.customer_name}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{formatDate(order.transaction_date)}</td>
                  <td className="px-6 py-3 text-sm text-gray-900 text-right font-medium">
                    {formatCurrency(order.grand_total)}
                  </td>
                  <td className="px-6 py-3">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                </tr>
              ))}
              {recentOrders.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                    No recent orders found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile card list */}
        <div className="md:hidden divide-y divide-gray-100">
          {recentOrders.map((order) => (
            <div key={order.name} className="px-4 py-3 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-brand-700">{order.name}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${getStatusColor(order.status)}`}>
                  {order.status}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">{order.customer_name}</span>
                <span className="font-medium text-gray-900">{formatCurrency(order.grand_total)}</span>
              </div>
              <div className="text-[10px] text-gray-400">{formatDate(order.transaction_date)}</div>
            </div>
          ))}
          {recentOrders.length === 0 && !loading && (
            <div className="px-4 py-8 text-center text-gray-400 text-sm">No recent orders found.</div>
          )}
        </div>
      </div>
    </div>
  );
}
