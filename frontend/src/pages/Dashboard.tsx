import { Activity, AlertTriangle, ShieldCheck, Server } from 'lucide-react';

export default function Dashboard() {
    const stats = [
        { label: 'Total Alerts', value: '1,234', change: '+12%', icon: AlertTriangle, color: 'text-red-500' },
        { label: 'Active Incidents', value: '5', change: '-2', icon: Activity, color: 'text-orange-500' },
        { label: 'Systems Monitored', value: '42', change: '0', icon: Server, color: 'text-blue-500' },
        { label: 'Security Score', value: '98%', change: '+1%', icon: ShieldCheck, color: 'text-green-500' },
    ];

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat) => (
                    <div key={stat.label} className="bg-card p-4 rounded-xl border border-border shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-muted-foreground text-sm font-medium">{stat.label}</span>
                            <stat.icon size={18} className={stat.color} />
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold">{stat.value}</span>
                            <span className="text-xs text-muted-foreground">{stat.change}</span>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-card p-6 rounded-xl border border-border shadow-sm min-h-[300px]">
                    <h3 className="font-semibold mb-4">Alert Trends</h3>
                    <div className="flex items-center justify-center h-full text-muted-foreground border-2 border-dashed border-muted rounded-lg">
                        Chart Placeholder
                    </div>
                </div>
                <div className="bg-card p-6 rounded-xl border border-border shadow-sm min-h-[300px]">
                    <h3 className="font-semibold mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="flex items-start gap-3 p-2 hover:bg-muted/50 rounded-lg text-sm">
                                <div className="w-2 h-2 mt-1.5 rounded-full bg-blue-500" />
                                <div>
                                    <p className="font-medium">Failed login attempt detected</p>
                                    <p className="text-muted-foreground text-xs">2 mins ago • Host-0{i}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
