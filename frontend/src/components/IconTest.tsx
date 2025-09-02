import React from "react";
import {
  LayoutDashboard,
  Upload,
  ShieldCheck,
  MonitorSmartphone,
  BarChart3,
  Settings,
  Users,
  Shield,
  Building2,
  UserPlus,
  FileImage,
  PlayCircle,
  Eye,
  Zap,
  DollarSign,
  Key,
  Layers,
} from "lucide-react";

export function IconTest() {
  const icons = [
    { name: "LayoutDashboard", icon: <LayoutDashboard className="h-6 w-6" /> },
    { name: "Users", icon: <Users className="h-6 w-6" /> },
    { name: "Shield", icon: <Shield className="h-6 w-6" /> },
    { name: "UserPlus", icon: <UserPlus className="h-6 w-6" /> },
    { name: "Key", icon: <Key className="h-6 w-6" /> },
    { name: "Building2", icon: <Building2 className="h-6 w-6" /> },
    { name: "FileImage", icon: <FileImage className="h-6 w-6" /> },
    { name: "Upload", icon: <Upload className="h-6 w-6" /> },
    { name: "Eye", icon: <Eye className="h-6 w-6" /> },
    { name: "ShieldCheck", icon: <ShieldCheck className="h-6 w-6" /> },
    { name: "Layers", icon: <Layers className="h-6 w-6" /> },
    { name: "MonitorSmartphone", icon: <MonitorSmartphone className="h-6 w-6" /> },
    { name: "PlayCircle", icon: <PlayCircle className="h-6 w-6" /> },
    { name: "Zap", icon: <Zap className="h-6 w-6" /> },
    { name: "BarChart3", icon: <BarChart3 className="h-6 w-6" /> },
    { name: "DollarSign", icon: <DollarSign className="h-6 w-6" /> },
    { name: "Settings", icon: <Settings className="h-6 w-6" /> },
  ];

  return (
    <div className="p-8 bg-background">
      <h2 className="text-2xl font-bold mb-6">Icon Test - All Sidebar Icons</h2>
      <div className="grid grid-cols-4 gap-4">
        {icons.map((item, index) => (
          <div key={index} className="flex flex-col items-center space-y-2 p-4 border rounded-lg bg-card">
            <div className="text-blue-600">
              {item.icon}
            </div>
            <span className="text-xs text-center font-medium">{item.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
