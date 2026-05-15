import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { TrendingUp, ShoppingCart, Package, DollarSign, ChevronRight } from 'lucide-react';
import { REPORTS, CATEGORIES, getReportsByCategory, getReportById } from '../lib/reportDefinitions';
import type { ReportCategory, ReportDef } from '../lib/reportDefinitions';
import ReportView from '../components/reports/ReportView';

const ICONS: Record<string, React.ReactNode> = {
  TrendingUp: <TrendingUp size={18} />,
  ShoppingCart: <ShoppingCart size={18} />,
  Package: <Package size={18} />,
  DollarSign: <DollarSign size={18} />,
};

export default function ReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const paramCategory = searchParams.get('cat') as ReportCategory | null;
  const paramReport = searchParams.get('id');

  const [activeCategory, setActiveCategory] = useState<ReportCategory>(paramCategory || 'sales');
  const [activeReport, setActiveReport] = useState<ReportDef | null>(
    paramReport ? getReportById(paramReport) ?? null : null,
  );

  // Sync URL → state on browser back/forward
  useEffect(() => {
    const cat = searchParams.get('cat') as ReportCategory | null;
    const id = searchParams.get('id');
    if (cat && CATEGORIES.some((c) => c.key === cat)) setActiveCategory(cat);
    setActiveReport(id ? getReportById(id) ?? null : null);
  }, [searchParams]);

  const selectCategory = (key: ReportCategory) => {
    setActiveCategory(key);
    setActiveReport(null);
    setSearchParams({ cat: key });
  };

  const selectReport = (r: ReportDef) => {
    setActiveReport(r);
    setSearchParams({ cat: activeCategory, id: r.id });
  };

  const goBack = () => {
    setActiveReport(null);
    setSearchParams({ cat: activeCategory });
  };

  const categoryReports = getReportsByCategory(activeCategory);

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="page-title">Reports</h1>
        <p className="text-gray-500 mt-1">Business intelligence and analytics</p>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg overflow-x-auto">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => { selectCategory(cat.key); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              activeCategory === cat.key
                ? 'bg-white shadow text-brand-700'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {ICONS[cat.icon]}
            {cat.label}
          </button>
        ))}
      </div>

      {/* Active Report or Report Grid */}
      {activeReport ? (
        <div>
          <button
            onClick={goBack}
            className="text-sm text-brand-600 hover:underline mb-4 flex items-center gap-1"
          >
            ← Back to {CATEGORIES.find((c) => c.key === activeCategory)?.label} reports
          </button>
          <ReportView report={activeReport} />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categoryReports.map((r) => (
            <button
              key={r.id}
              onClick={() => selectReport(r)}
              className="card p-5 text-left hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 group-hover:text-brand-700 transition-colors">
                    {r.title}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">{r.description}</p>
                </div>
                <ChevronRight size={18} className="text-gray-400 group-hover:text-brand-600 mt-1 flex-shrink-0" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
