import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, ShieldAlert, BookOpen, Menu, Bell } from 'lucide-react';
import clsx from 'clsx';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function MainLayout() {
    const location = useLocation();
    const [sidebarOpen, setSidebarOpen] = useState(true);

    const navItems = [
        { path: '/', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/investigate', label: 'Investigation', icon: ShieldAlert },
        { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
    ];

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden">
            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: sidebarOpen ? 240 : 64 }}
                className="bg-card border-r border-border flex flex-col z-20"
            >
                <div className="p-4 flex items-center justify-between border-b border-border h-16">
                    <AnimatePresence>
                        {sidebarOpen && (
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="font-bold text-xl text-primary truncate"
                            >
                                SIEM Pilot
                            </motion.span>
                        )}
                    </AnimatePresence>
                    <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 hover:bg-muted rounded text-muted-foreground">
                        <Menu size={20} />
                    </button>
                </div>

                <nav className="flex-1 p-2 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={clsx(
                                    "flex items-center gap-3 p-3 rounded-md transition-colors",
                                    isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                )}
                            >
                                <Icon size={20} />
                                {sidebarOpen && <span className="whitespace-nowrap">{item.label}</span>}
                            </Link>
                        )
                    })}
                </nav>
            </motion.aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-16 border-b border-border bg-card flex items-center justify-between px-6">
                    <h1 className="text-lg font-semibold">
                        {navItems.find(i => i.path === location.pathname)?.label || 'Overview'}
                    </h1>
                    <div className="flex items-center gap-4">
                        <button className="relative p-2 text-muted-foreground hover:bg-muted rounded-full">
                            <Bell size={20} />
                            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                        </button>
                        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold">
                            A
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-auto p-6 bg-muted/20">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
