import { useState, useEffect, useCallback } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Suspense } from 'react';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import MobileNav from '../components/MobileNav';

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Close sidebar on route change (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  // Close sidebar on Escape key
  useEffect(() => {
    if (!sidebarOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSidebarOpen(false);
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [sidebarOpen]);

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [sidebarOpen]);

  const toggleSidebar = useCallback(() => setSidebarOpen(p => !p), []);
  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  return (
    <div className="min-h-[var(--vh-full,100vh)] bg-gray-50 dark:bg-slate-950">
      {/* Skip-to-content for keyboard users */}
      <a href="#main-content" className="skip-to-content">
        Skip to main content
      </a>

      <Navbar onMenuToggle={toggleSidebar} />

      {/* Desktop sidebar — always visible at lg+ */}
      <nav className="hidden lg:block" aria-label="Main navigation">
        <Sidebar />
      </nav>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <>
          <div className="overlay-backdrop lg:hidden" onClick={closeSidebar} aria-hidden="true" />
          <nav className="fixed inset-y-0 left-0 z-50 w-[280px] lg:hidden slide-in-left" aria-label="Mobile navigation">
            <Sidebar mobile onClose={closeSidebar} />
          </nav>
        </>
      )}

      {/* Main content area */}
      <main id="main-content" className="lg:ml-[260px] mt-[var(--navbar-height)] pb-[calc(var(--mobile-nav-height)+var(--safe-bottom,0px))] lg:pb-0 page-container dark:bg-slate-950">
        <Suspense fallback={<div className="flex items-center justify-center h-64"><div className="spinner" role="status"><span className="sr-only">Loading…</span></div></div>}>
          <Outlet />
        </Suspense>
      </main>

      {/* Mobile bottom navigation — visible below lg */}
      <MobileNav onMorePress={toggleSidebar} />
    </div>
  );
}
